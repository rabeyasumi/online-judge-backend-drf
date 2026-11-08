from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .services.contest_scoring import calculate_student_contest_score
from django.db.models import Q

from accounts.models import Student
from problems.models import Element
from contests.models import Contest
from .languages import LANGUAGES
from .judge import execute_code, JudgeServiceError

from django.db import transaction

from .models import Submission, Standings
from .serializers import (
    SubmissionListSerializer,
    StandingsSerializer
)


from .Pagination import ProblemPagination


def update_contest_ranks(contest):

    standings = Standings.objects.filter(
        contest=contest
    ).order_by(
        '-rating',
        'student_id'
    )

    current_rank = 0
    previous_rating = None

    for index, standing in enumerate(standings):

        current_rating = round(float(standing.rating), 2)

        if (
            previous_rating is None
            or current_rating != previous_rating
        ):
            current_rank = index + 1

        if standing.rank != current_rank:
            standing.rank = current_rank
            standing.save(update_fields=['rank'])

        previous_rating = current_rating

def update_contest_standing(submission):

    contest = submission.contest
    student = submission.student

    if contest is None:
        return
    
    if not (
        contest.start_datetime <= submission.submitted_at <= contest.end_datetime
    ):
        return

    # Calculate solved count and rating using our scoring formula
    score_data = calculate_student_contest_score(
        student,
        contest
    )

    solved = score_data['solved']
    rating = score_data['rating']

    # Calculate ICPC-style penalty separately
    student_submissions = Submission.objects.filter(
        contest=contest,
        student=student,
        submitted_at__gte=contest.start_datetime,
        submitted_at__lt=contest.end_datetime
    ).select_related(
        'element'
    ).order_by(
        'submitted_at',
        'id'
    )

    problem_stats = {}

    for item in student_submissions:

        problem_id = item.element_id

        if problem_id not in problem_stats:
            problem_stats[problem_id] = {
                'accepted': None,
                'wrong_attempts': 0
            }

        stats = problem_stats[problem_id]

        if stats['accepted'] is not None:
            continue

        if item.verdict == 'Accepted':
            stats['accepted'] = item

        elif item.verdict == 'Wrong Answer':
            stats['wrong_attempts'] += 1

    penalty = 0

    for stats in problem_stats.values():

        accepted = stats['accepted']

        if accepted is None:
            continue

        elapsed = accepted.submitted_at - contest.start_datetime

        ac_minutes = max(
            0,
            int(elapsed.total_seconds() // 60)
        )

        penalty += (
            ac_minutes
            + stats['wrong_attempts'] * 20
        )

    # Save contest standing
    with transaction.atomic():

        Standings.objects.update_or_create(
            contest=contest,
            student=student,
            defaults={
                'solved': solved,
                'penalty': penalty,
                'rating': rating
            }
        )
        update_contest_ranks(contest)
        

class ContestStandingsView(generics.ListAPIView):

    serializer_class = StandingsSerializer
    permission_classes = [AllowAny]
    pagination_class = ProblemPagination 
    

    def get_queryset(self):

        contest = get_object_or_404(
            Contest,
            id=self.kwargs['contest_id']
        )

        return Standings.objects.filter(
            contest=contest
        ).select_related(
            'student'
        ).order_by(
            '-rating',
            'penalty',
            '-solved',
            'student_id'
        )


class LanguageListView(APIView):

    permission_classes = [AllowAny]

    def get(self, request):
        return Response(LANGUAGES)


class SubmitCodeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 1. Get request data
        problem_id = request.data.get('problem_id')
        language = request.data.get('language')
        code = request.data.get('code')

        # 2. Validate request data
        if not problem_id or not language or not isinstance(code, str) or not code.strip():
            return Response(
                {
                    'error': 'problem_id, language and non-empty code are required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            problem_id = int(problem_id)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid problem_id.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not isinstance(code, str):
            return Response(
                {'error': 'Code must be a string.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not any(item['language'] == language for item in LANGUAGES):
            return Response(
                {'error': 'Unsupported programming language.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Get logged-in student's profile
        student = Student.objects.filter(user=request.user).first()

        if student is None:
            return Response(
                {'error': 'Student profile not found.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # 4. Get problem and its contest
        problem = Element.objects.filter(
            id=problem_id
        ).select_related('contest').first()

        if problem is None:
            return Response(
                {'error': 'Problem not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # 5. Get hidden test cases
        test_cases = list(problem.test_cases.all())

        if not test_cases:
            return Response(
                {'error': 'No test cases available for this problem.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 6. Create submission with Pending verdict
        submission = Submission.objects.create(
            student=student,
            element=problem,
            contest=problem.contest,
            code=code,
            language=language
        )

        passed_testcases = 0
        total_execution_time = 0
        maximum_memory = 0

        
        # 7. Check compilation before running test cases
        try:
            compilation_result = execute_code(
                code=code,
                language=language,
                compile_only=True
            )

            compilation_status = str(
                compilation_result.get('compilation_status')
            )

            # Compilation failed
            if compilation_status == '1':

                submission.verdict = 'Compilation Error'
                submission.save()

                if submission.contest is not None:
                    update_contest_standing(submission)

                return Response(
                    {
                        'submission_id': submission.id,
                        'problem_id': problem.id,
                        'verdict': submission.verdict,
                        'compiler_output': compilation_result['output'],
                        'passed_testcases': 0,
                        'total_testcases': len(test_cases),
                        'execution_time': None,
                        'memory': None,
                        'submitted_at': submission.submitted_at
                    },
                    status=status.HTTP_201_CREATED
                )

            # Unknown compilation response
            if compilation_status != '0':
                raise JudgeServiceError(
                    'Could not verify compilation status.'
                )

            # 8. Compilation successful: execute hidden test cases
            passed_testcases = 0
            total_execution_time = 0
            maximum_memory = 0

            for test_case in test_cases:

                result = execute_code(
                    code=code,
                    language=language,
                    stdin=test_case.input_data
                )

                actual_output = result['output']
                expected_output = test_case.expected_output

                actual = ' '.join(actual_output.split())
                expected = ' '.join(expected_output.split())

                if result['execution_time'] is not None:
                    total_execution_time += float(
                        result['execution_time']
                    )

                if result['memory'] is not None:
                    maximum_memory = max(
                        maximum_memory,
                        float(result['memory'])
                    )

                if actual != expected:
                    submission.verdict = 'Wrong Answer'
                    break

                passed_testcases += 1

            else:
                submission.verdict = 'Accepted'

        except JudgeServiceError:
            submission.verdict = 'Judge Error'

        except (TypeError, ValueError, KeyError):
            submission.verdict = 'Judge Error'

        submission.execution_time = total_execution_time
        submission.memory = maximum_memory

        # Save final verdict and execution details
        submission.save()

        # Update contest standing after final verdict
        if submission.verdict != 'Judge Error':
            update_contest_standing(submission)


        # 9. Return submission result
        return Response(
            {
                'submission_id': submission.id,
                'problem_id': problem.id,
                'verdict': submission.verdict,
                'passed_testcases': passed_testcases,
                'total_testcases': len(test_cases),
                'execution_time': submission.execution_time,
                'memory': submission.memory,
                'submitted_at': submission.submitted_at
            },
            status=status.HTTP_201_CREATED
        )

class MySubmissionListView(generics.ListAPIView):
    """GET /api/submissions/my/ -> logged-in student's submissions, newest first.
    Optional filters: ?problem_id=<id>  ?contest=<id>"""

    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProblemPagination 

    def get_queryset(self):
        qs = Submission.objects.filter(
            student__user=self.request.user
        ).select_related('element', 'student')

        problem_id = self.request.query_params.get('problem_id')
        contest = self.request.query_params.get('contest')
        if problem_id and problem_id.isdigit():
            qs = qs.filter(element_id=int(problem_id))
        if contest and contest.isdigit():
            qs = qs.filter(contest_id=int(contest))

        return qs.order_by('-submitted_at', '-id')


class AllSubmissionListView(generics.ListAPIView):
    """
    GET /api/submissions/all/

    Optional filters:
    ?verdict=Accepted
    ?language=Python
    ?contest_id=2
    ?problem_name=Add two numbers
    ?handle=sumi
    """

    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = ProblemPagination  

    def get_queryset(self):
        qs = Submission.objects.select_related(
            'student',
            'element',
            'contest'
        )

        verdict = self.request.query_params.get('verdict')
        language = self.request.query_params.get('language')
        contest_id = self.request.query_params.get('contest_id')
        problem_name = self.request.query_params.get('problem_name')
        handle = self.request.query_params.get('handle')

        if verdict:
            qs = qs.filter(verdict__iexact=verdict.strip())

        if language:
            qs = qs.filter(language__iexact=language.strip())

        if contest_id and contest_id.isdigit():
            qs = qs.filter(contest_id=int(contest_id))

        if problem_name:
            qs = qs.filter(
                element__pname__icontains=problem_name.strip()
            )

        if handle:
            qs = qs.filter(
                student__handle__icontains=handle.strip()
            )

        return qs.order_by('-submitted_at', '-id')