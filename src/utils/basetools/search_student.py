import pandas as pd
import json
from datetime import datetime
from typing import Optional, Dict, List, Any, Union
import os
from pydantic import BaseModel, Field, field_validator, model_validator

# Pydantic Models for Input/Output
class StudentSearchInput(BaseModel):
    """Input model for student search"""
    student_id: Optional[str] = None
    student_name: Optional[str] = None
    from_date: Optional[str] = None
    to_date: Optional[str] = None
    subject: Optional[str] = None
    student_class: Optional[str] = None
    limit: Optional[int] = None

    @field_validator('from_date', 'to_date')
    @classmethod
    def validate_date_format(cls, v):
        if v is not None:
            try:
                datetime.strptime(v, '%Y-%m-%d')
            except ValueError:
                raise ValueError('Date must be in format YYYY-MM-DD')
        return v

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.to_date is not None and self.from_date is not None:
            from_date = datetime.strptime(self.from_date, '%Y-%m-%d')
            to_date = datetime.strptime(self.to_date, '%Y-%m-%d')
            if to_date < from_date:
                raise ValueError('to_date must be after from_date')
        return self

class StudentResult(BaseModel):
    """Individual student result model"""
    result_id: int
    student_id: str
    student_class: str
    subject: str
    test_date: str
    test_number: int
    question_number: int
    topic: str
    level: str
    is_correct: bool
    time_taken_seconds: int
    student_ability: str

class SearchSummary(BaseModel):
    """Search summary model"""
    total_results: int
    unique_students: int
    date_range: Dict[str, Optional[str]]
    subjects: List[str]

class StudentSearchOutput(BaseModel):
    """Output model for student search"""
    success: bool
    summary: SearchSummary
    results: List[StudentResult]
    error: Optional[str] = None

class StudentStatsInput(BaseModel):
    """Input model for student statistics"""
    student_id: str = Field(description="Student ID to get stats for")

class SubjectPerformance(BaseModel):
    """Subject performance model"""
    total_questions: int
    correct_answers: int
    accuracy: float
    avg_time_seconds: float

class LevelPerformance(BaseModel):
    """Level performance model"""
    total_questions: int
    correct_answers: int
    accuracy: float

class OverallStats(BaseModel):
    """Overall statistics model"""
    total_questions: int
    correct_answers: int
    accuracy_percentage: float
    avg_time_seconds: float

class StudentStatsOutput(BaseModel):
    """Output model for student statistics"""
    success: bool
    student_id: str
    student_class: str
    student_ability: str
    overall_stats: OverallStats
    subject_performance: Dict[str, SubjectPerformance]
    level_performance: Dict[str, LevelPerformance]
    test_dates: List[str]
    error: Optional[str] = None

class LatestTestInput(BaseModel):
    """Input model for latest test summary"""
    student_id: Optional[str] = Field(None, description="Student ID to get latest test for (optional)")

class SubjectStats(BaseModel):
    """Subject statistics model"""
    latest_test_date: str
    question_levels: Dict[str, int]

class LatestTestOutput(BaseModel):
    """Output model for latest test summary"""
    success: bool
    student_id: str
    unique_students: int
    subjects: Dict[str, SubjectStats]
    error: Optional[str] = None

# Global DataFrame for caching
_student_data_df = None

def _load_student_data(csv_file_path: Optional[str] = None) -> pd.DataFrame:
    """Load CSV data into pandas DataFrame"""
    global _student_data_df
    
    if _student_data_df is not None:
        return _student_data_df
    
    if csv_file_path is None:
        # Default path relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        csv_file_path = os.path.join(current_dir, "../../data/mock_data/student_results_professional.csv")
    
    try:
        _student_data_df = pd.read_csv(csv_file_path)
        # Convert test_date to datetime
        _student_data_df['test_date'] = pd.to_datetime(_student_data_df['test_date'])
        return _student_data_df
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV file not found at: {csv_file_path}")
    except Exception as e:
        raise Exception(f"Error loading CSV file: {str(e)}")

def search_student(search_input: StudentSearchInput) -> StudentSearchOutput:
    """
    Search for student results based on various criteria
    
    Args:
        search_input: StudentSearchInput model with search criteria
        
    Returns:
        StudentSearchOutput model containing search results
    """
    try:
        df = _load_student_data()
        
        # Start with full dataset
        filtered_df = df.copy()
        
        # Filter by student_id or student_name
        if search_input.student_id:
            filtered_df = filtered_df[filtered_df['student_id'].astype(str).str.contains(str(search_input.student_id), case=False, na=False)]
        elif search_input.student_name:
            filtered_df = filtered_df[filtered_df['student_id'].astype(str).str.contains(str(search_input.student_name), case=False, na=False)]
        
        # Filter by date range
        if search_input.from_date:
            from_date_dt = pd.to_datetime(search_input.from_date)
            filtered_df = filtered_df[filtered_df['test_date'] >= from_date_dt]
        
        if search_input.to_date:
            to_date_dt = pd.to_datetime(search_input.to_date)
            filtered_df = filtered_df[filtered_df['test_date'] <= to_date_dt]
        
        # Filter by subject
        if search_input.subject:
            filtered_df = filtered_df[filtered_df['subject'].str.contains(search_input.subject, case=False, na=False)]
        
        # Filter by class
        if search_input.student_class:
            filtered_df = filtered_df[filtered_df['student_class'].str.contains(search_input.student_class, case=False, na=False)]
        
        # Apply limit
        if search_input.limit and search_input.limit > 0:
            filtered_df = filtered_df.head(search_input.limit)
        
        # Convert to StudentResult objects
        results = []
        for _, row in filtered_df.iterrows():
            result = StudentResult(
                result_id=int(row['result_id']),
                student_id=str(row['student_id']),
                student_class=row['student_class'],
                subject=row['subject'],
                test_date=row['test_date'].strftime('%Y-%m-%d'),
                test_number=int(row['test_number']),
                question_number=int(row['question_number']),
                topic=row['topic'],
                level=row['level'],
                is_correct=bool(row['is_correct']),
                time_taken_seconds=int(row['time_taken_seconds']),
                student_ability=row['student_ability']
            )
            results.append(result)
        
        # Create summary
        summary = SearchSummary(
            total_results=len(results),
            unique_students=len(filtered_df['student_id'].unique()) if len(results) > 0 else 0,
            date_range={
                "from": filtered_df['test_date'].min().strftime('%Y-%m-%d') if len(results) > 0 else None,
                "to": filtered_df['test_date'].max().strftime('%Y-%m-%d') if len(results) > 0 else None
            },
            subjects=list(filtered_df['subject'].unique()) if len(results) > 0 else []
        )
        
        return StudentSearchOutput(
            success=True,
            summary=summary,
            results=results
        )
        
    except Exception as e:
        return StudentSearchOutput(
            success=False,
            error=str(e),
            summary=SearchSummary(total_results=0, unique_students=0, date_range={"from": None, "to": None}, subjects=[]),
            results=[]
        )

def get_student_stats(stats_input: StudentStatsInput) -> StudentStatsOutput:
    """
    Get comprehensive statistics for a specific student
    
    Args:
        stats_input: StudentStatsInput model with student ID
        
    Returns:
        StudentStatsOutput model containing student statistics
    """
    try:
        df = _load_student_data()
        
        student_df = df[df['student_id'].astype(str) == str(stats_input.student_id)]
        
        if len(student_df) == 0:
            return StudentStatsOutput(
                success=False,
                error=f"No data found for student_id: {stats_input.student_id}",
                student_id=stats_input.student_id,
                student_class="",
                student_ability="",
                overall_stats=OverallStats(total_questions=0, correct_answers=0, accuracy_percentage=0, avg_time_seconds=0),
                subject_performance={},
                level_performance={},
                test_dates=[]
            )
        
        # Calculate statistics
        total_questions = len(student_df)
        correct_answers = int(student_df['is_correct'].sum())
        accuracy = (correct_answers / total_questions) * 100 if total_questions > 0 else 0
        
        # Subject-wise performance
        subject_stats = {}
        for subject in student_df['subject'].unique():
            subject_data = student_df[student_df['subject'] == subject]
            subject_stats[subject] = SubjectPerformance(
                total_questions=len(subject_data),
                correct_answers=int(subject_data['is_correct'].sum()),
                accuracy=float((subject_data['is_correct'].sum() / len(subject_data)) * 100),
                avg_time_seconds=float(subject_data['time_taken_seconds'].mean())
            )
        
        # Level-wise performance
        level_stats = {}
        for level in student_df['level'].unique():
            level_data = student_df[student_df['level'] == level]
            level_stats[level] = LevelPerformance(
                total_questions=len(level_data),
                correct_answers=int(level_data['is_correct'].sum()),
                accuracy=float((level_data['is_correct'].sum() / len(level_data)) * 100)
            )
        
        return StudentStatsOutput(
            success=True,
            student_id=stats_input.student_id,
            student_class=student_df['student_class'].iloc[0],
            student_ability=student_df['student_ability'].iloc[0],
            overall_stats=OverallStats(
                total_questions=total_questions,
                correct_answers=correct_answers,
                accuracy_percentage=float(accuracy),
                avg_time_seconds=float(student_df['time_taken_seconds'].mean())
            ),
            subject_performance=subject_stats,
            level_performance=level_stats,
            test_dates=sorted(student_df['test_date'].dt.strftime('%Y-%m-%d').unique().tolist())
        )
        
    except Exception as e:
        return StudentStatsOutput(
            success=False,
            error=str(e),
            student_id=stats_input.student_id,
            student_class="",
            student_ability="",
            overall_stats=OverallStats(total_questions=0, correct_answers=0, accuracy_percentage=0, avg_time_seconds=0),
            subject_performance={},
            level_performance={},
            test_dates=[]
        )

def get_latest_test_summary(latest_input: LatestTestInput) -> LatestTestOutput:
    """
    Get the latest test results summary for each subject with question level breakdown
    
    Args:
        latest_input: LatestTestInput model with optional student ID
        
    Returns:
        LatestTestOutput model containing latest test summary for each subject
    """
    try:
        df = _load_student_data()
        
        # Filter by student if provided
        if latest_input.student_id:
            filtered_df = df[df['student_id'].astype(str) == str(latest_input.student_id)]
            if len(filtered_df) == 0:
                return LatestTestOutput(
                    success=False,
                    error=f"No data found for student_id: {latest_input.student_id}",
                    student_id=latest_input.student_id,
                    unique_students=0,
                    subjects={}
                )
        else:
            filtered_df = df.copy()
        
        # Group by subject and level to count questions from latest test for each subject
        subject_level_stats = {}
        
        # Get unique subjects
        subjects = filtered_df['subject'].unique()
        
        for subject in subjects:
            subject_data = filtered_df[filtered_df['subject'] == subject]
            
            # Find the latest test date for this specific subject
            latest_date_for_subject = subject_data['test_date'].max()
            
            # Get all results from the latest test date for this subject
            latest_subject_test_df = subject_data[subject_data['test_date'] == latest_date_for_subject]
            
            # Count questions by level
            level_counts = {
                "Nhận biết": 0,
                "Thông hiểu": 0,
                "Vận dụng thấp": 0,
                "Vận dụng cao": 0
            }
            
            # Count actual questions for each level
            for level in latest_subject_test_df['level'].unique():
                level_data = latest_subject_test_df[latest_subject_test_df['level'] == level]
                level_counts[level] = len(level_data)
            
            subject_level_stats[subject] = SubjectStats(
                latest_test_date=latest_date_for_subject.strftime('%Y-%m-%d'),
                question_levels=level_counts
            )
        
        return LatestTestOutput(
            success=True,
            student_id=latest_input.student_id or "all_students",
            unique_students=len(filtered_df['student_id'].unique()),
            subjects=subject_level_stats
        )
        
    except Exception as e:
        return LatestTestOutput(
            success=False,
            error=str(e),
            student_id=latest_input.student_id or "all_students",
            unique_students=0,
            subjects={}
        )

# Tool functions for AgentClient usage
def search_student_tool_func(student_id: Optional[str] = None, subject: Optional[str] = None, student_class: Optional[str] = None, limit: int = 10):
    """Search for student information - Tool function for AgentClient"""
    search_input = StudentSearchInput(
        student_id=student_id,
        subject=subject,
        student_class=student_class,
        limit=limit
    )
    result = search_student(search_input)
    return result.model_dump()

def get_student_stats_tool_func(student_id: str):
    """Get comprehensive statistics for a specific student - Tool function for AgentClient"""
    stats_input = StudentStatsInput(student_id=student_id)
    result = get_student_stats(stats_input)
    return result.model_dump()

def get_latest_test_tool_func(student_id: Optional[str] = "20250001"):
    """Get latest test summary for student - Tool function for AgentClient"""
    latest_input = LatestTestInput(student_id=student_id)
    result = get_latest_test_summary(latest_input)
    print(f"Latest test result: {result}")
    return result.model_dump()

# Example usage
if __name__ == "__main__":
    # Test the functions
    get_latest_test_tool_func("20250001")