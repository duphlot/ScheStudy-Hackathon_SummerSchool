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
    subject: str
    test_date: str
    topic: str
    level: str
    # Note: All records in this dataset represent incorrect answers

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
    """Subject performance model - showing only wrong answers"""
    total_wrong_questions: int
    wrong_topics: Dict[str, int]

class LevelPerformance(BaseModel):
    """Level performance model - showing only wrong answers"""
    total_wrong_questions: int
    wrong_topics: Dict[str, int]

class OverallStats(BaseModel):
    """Overall statistics model - showing only wrong answers"""
    total_wrong_questions: int
    subjects_with_errors: List[str]
    levels_with_errors: List[str]

class StudentStatsOutput(BaseModel):
    """Output model for student statistics"""
    success: bool
    student_id: str
    overall_stats: OverallStats
    subject_performance: Dict[str, SubjectPerformance]
    level_performance: Dict[str, LevelPerformance]
    test_dates: List[str]
    error: Optional[str] = None

class LatestTestInput(BaseModel):
    """Input model for latest test summary"""
    student_id: Optional[str] = Field(None, description="Student ID to get latest test for (optional)")

class SecondLatestTestInput(BaseModel):
    """Input model for second latest test summary"""
    student_id: Optional[str] = Field(None, description="Student ID to get second latest test for (optional)")

class TopicStats(BaseModel):
    """Topic statistics model for wrong answers"""
    wrong_questions_count: int
    topic_name: str

class LevelStats(BaseModel):
    """Level statistics with topic breakdown for wrong answers"""
    total_wrong_questions: int
    wrong_topics: Dict[str, int]  # topic_name -> count of wrong questions

class SubjectStats(BaseModel):
    """Subject statistics model"""
    latest_test_date: str
    level_breakdown: Dict[str, LevelStats]

class LatestTestOutput(BaseModel):
    """Output model for latest test summary"""
    success: bool
    student_id: str
    unique_students: int
    subjects: Dict[str, SubjectStats]
    error: Optional[str] = None

class SecondLatestTestOutput(BaseModel):
    """Output model for second latest test summary"""
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
                subject=row['subject'],
                test_date=row['test_date'].strftime('%Y-%m-%d'),
                topic=row['topic'],
                level=row['level']
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
    Get comprehensive statistics for a specific student showing wrong answers breakdown
    
    Args:
        stats_input: StudentStatsInput model with student ID
        
    Returns:
        StudentStatsOutput model containing student wrong answers statistics
    """
    try:
        df = _load_student_data()
        
        student_df = df[df['student_id'].astype(str) == str(stats_input.student_id)]
        
        if len(student_df) == 0:
            return StudentStatsOutput(
                success=False,
                error=f"No data found for student_id: {stats_input.student_id}",
                student_id=stats_input.student_id,
                overall_stats=OverallStats(
                    total_wrong_questions=0, 
                    subjects_with_errors=[], 
                    levels_with_errors=[]
                ),
                subject_performance={},
                level_performance={},
                test_dates=[]
            )
        
        # Calculate overall statistics (all are wrong answers)
        total_wrong_questions = len(student_df)
        subjects_with_errors = list(student_df['subject'].unique())
        levels_with_errors = list(student_df['level'].unique())
        
        # Subject-wise performance (wrong answers)
        subject_stats = {}
        for subject in student_df['subject'].unique():
            subject_data = student_df[student_df['subject'] == subject]
            
            # Count wrong answers by topic for this subject
            topic_counts = {}
            for topic in subject_data['topic'].unique():
                topic_data = subject_data[subject_data['topic'] == topic]
                topic_counts[topic] = len(topic_data)
            
            subject_stats[subject] = SubjectPerformance(
                total_wrong_questions=len(subject_data),
                wrong_topics=topic_counts
            )
        
        # Level-wise performance (wrong answers)
        level_stats = {}
        for level in student_df['level'].unique():
            level_data = student_df[student_df['level'] == level]
            
            # Count wrong answers by topic for this level
            topic_counts = {}
            for topic in level_data['topic'].unique():
                topic_data = level_data[level_data['topic'] == topic]
                topic_counts[topic] = len(topic_data)
            
            level_stats[level] = LevelPerformance(
                total_wrong_questions=len(level_data),
                wrong_topics=topic_counts
            )
        
        return StudentStatsOutput(
            success=True,
            student_id=stats_input.student_id,
            overall_stats=OverallStats(
                total_wrong_questions=total_wrong_questions,
                subjects_with_errors=subjects_with_errors,
                levels_with_errors=levels_with_errors
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
            overall_stats=OverallStats(
                total_wrong_questions=0, 
                subjects_with_errors=[], 
                levels_with_errors=[]
            ),
            subject_performance={},
            level_performance={},
            test_dates=[]
        )

def get_latest_test_summary(latest_input: LatestTestInput) -> LatestTestOutput:
    """
    Get the latest test results summary showing wrong answers by level and topic
    
    Args:
        latest_input: LatestTestInput model with optional student ID
        
    Returns:
        LatestTestOutput model containing latest test summary with wrong answers breakdown
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
        
        # Group by subject to analyze wrong answers from latest test for each subject
        subject_level_stats = {}
        
        # Get unique subjects
        subjects = filtered_df['subject'].unique()
        
        for subject in subjects:
            subject_data = filtered_df[filtered_df['subject'] == subject]
            
            # Find the latest test date for this specific subject
            latest_date_for_subject = subject_data['test_date'].max()
            
            # Get all results from the latest test date for this subject
            latest_subject_test_df = subject_data[subject_data['test_date'] == latest_date_for_subject]
            
            # Analyze wrong answers by level and topic
            level_breakdown = {}
            
            # Process each level
            for level in latest_subject_test_df['level'].unique():
                level_data = latest_subject_test_df[latest_subject_test_df['level'] == level]
                
                # Count wrong answers by topic for this level
                topic_counts = {}
                for topic in level_data['topic'].unique():
                    topic_data = level_data[level_data['topic'] == topic]
                    topic_counts[topic] = len(topic_data)
                
                level_breakdown[level] = LevelStats(
                    total_wrong_questions=len(level_data),
                    wrong_topics=topic_counts
                )
            
            subject_level_stats[subject] = SubjectStats(
                latest_test_date=latest_date_for_subject.strftime('%Y-%m-%d'),
                level_breakdown=level_breakdown
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

def get_second_latest_test_summary(second_latest_input: SecondLatestTestInput) -> SecondLatestTestOutput:
    """
    Get the second latest test results summary showing wrong answers by level and topic
    
    Args:
        second_latest_input: SecondLatestTestInput model with optional student ID
        
    Returns:
        SecondLatestTestOutput model containing second latest test summary with wrong answers breakdown
    """
    try:
        df = _load_student_data()
        
        # Filter by student if provided
        if second_latest_input.student_id:
            filtered_df = df[df['student_id'].astype(str) == str(second_latest_input.student_id)]
            if len(filtered_df) == 0:
                return SecondLatestTestOutput(
                    success=False,
                    error=f"No data found for student_id: {second_latest_input.student_id}",
                    student_id=second_latest_input.student_id,
                    unique_students=0,
                    subjects={}
                )
        else:
            filtered_df = df.copy()
        
        # Group by subject to analyze wrong answers from second latest test for each subject
        subject_level_stats = {}
        
        # Get unique subjects
        subjects = filtered_df['subject'].unique()
        
        for subject in subjects:
            subject_data = filtered_df[filtered_df['subject'] == subject]
            
            # Find the second latest test date for this specific subject
            unique_dates = sorted(subject_data['test_date'].unique(), reverse=True)
            
            if len(unique_dates) < 2:
                # Skip this subject if there's no second latest date
                continue
            
            second_latest_date_for_subject = unique_dates[1]
            
            # Get all results from the second latest test date for this subject
            second_latest_subject_test_df = subject_data[subject_data['test_date'] == second_latest_date_for_subject]
            
            # Analyze wrong answers by level and topic
            level_breakdown = {}
            
            # Process each level
            for level in second_latest_subject_test_df['level'].unique():
                level_data = second_latest_subject_test_df[second_latest_subject_test_df['level'] == level]
                
                # Count wrong answers by topic for this level
                topic_counts = {}
                for topic in level_data['topic'].unique():
                    topic_data = level_data[level_data['topic'] == topic]
                    topic_counts[topic] = len(topic_data)
                
                level_breakdown[level] = LevelStats(
                    total_wrong_questions=len(level_data),
                    wrong_topics=topic_counts
                )
            
            subject_level_stats[subject] = SubjectStats(
                latest_test_date=second_latest_date_for_subject.strftime('%Y-%m-%d'),
                level_breakdown=level_breakdown
            )
        
        return SecondLatestTestOutput(
            success=True,
            student_id=second_latest_input.student_id or "all_students",
            unique_students=len(filtered_df['student_id'].unique()),
            subjects=subject_level_stats
        )
        
    except Exception as e:
        return SecondLatestTestOutput(
            success=False,
            error=str(e),
            student_id=second_latest_input.student_id or "all_students",
            unique_students=0,
            subjects={}
        )

def analyze_wrong_answers_by_level(student_id: str, level: str = "Nhận biết") -> Dict[str, Any]:
    """
    Analyze wrong answers for a specific student and level
    
    Args:
        student_id: Student ID to analyze
        level: Level to analyze (default: "Nhận biết")
        
    Returns:
        Dictionary containing analysis of wrong answers by subject and topic
    """
    latest_input = LatestTestInput(student_id=student_id)
    result = get_latest_test_summary(latest_input)
    
    if not result.success:
        return {"error": result.error}
    
    analysis = {
        "student_id": student_id,
        "level": level,
        "subjects": {}
    }
    
    total_wrong_questions = 0
    
    for subject_name, subject_stats in result.subjects.items():
        if level in subject_stats.level_breakdown:
            level_stats = subject_stats.level_breakdown[level]
            
            analysis["subjects"][subject_name] = {
                "total_wrong_questions": level_stats.total_wrong_questions,
                "wrong_topics": level_stats.wrong_topics,
                "latest_test_date": subject_stats.latest_test_date
            }
            
            total_wrong_questions += level_stats.total_wrong_questions
    
    analysis["total_wrong_questions_in_level"] = total_wrong_questions
    
    return analysis

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

def get_second_latest_test_tool_func(student_id: Optional[str] = "20250001"):
    """Get second latest test summary for student - Tool function for AgentClient"""
    second_latest_input = SecondLatestTestInput(student_id=student_id)
    result = get_second_latest_test_summary(second_latest_input)
    print(f"Second latest test result: {result}")
    return result.model_dump()

def analyze_wrong_answers_by_level_tool_func(student_id: str, level: str = "Nhận biết"):
    """Analyze wrong answers for a specific level - Tool function for AgentClient"""
    result = analyze_wrong_answers_by_level(student_id, level)
    return result

# Example usage
if __name__ == "__main__":
    # Test the functions
    print("=== Latest Test Summary ===")
    get_latest_test_tool_func("20250001")
    
    print("\n=== Second Latest Test Summary ===")
    get_second_latest_test_tool_func("20250001")
    
    print("\n=== Analyze 'Nhận biết' Level ===")
    nhan_biet_analysis = analyze_wrong_answers_by_level_tool_func("20250001", "Nhận biết")
    print(f"Analysis for 'Nhận biết' level: {nhan_biet_analysis}")
    
    print("\n=== Analyze 'Thông hiểu' Level ===")
    thong_hieu_analysis = analyze_wrong_answers_by_level_tool_func("20250001", "Thông hiểu")
    print(f"Analysis for 'Thông hiểu' level: {thong_hieu_analysis}")