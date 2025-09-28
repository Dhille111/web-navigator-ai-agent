"""
Storage utilities for saving and exporting data in various formats
"""

import json
import csv
import os
import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path
import pandas as pd
from dataclasses import dataclass, asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ExportConfig:
    """Configuration for data export"""
    output_dir: str = "exports"
    json_format: bool = True
    csv_format: bool = True
    include_metadata: bool = True
    include_timestamps: bool = True
    pretty_print: bool = True


@dataclass
class TaskResult:
    """Result of a task execution"""
    task_id: str
    status: str  # success, error, partial
    instruction: str
    results: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    timestamp: datetime
    execution_time: float
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'task_id': self.task_id,
            'status': self.status,
            'instruction': self.instruction,
            'results': self.results,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'execution_time': self.execution_time,
            'error_message': self.error_message
        }


class DataStorage:
    """Storage manager for task results and data export"""
    
    def __init__(self, config: Optional[ExportConfig] = None):
        self.config = config or ExportConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.output_dir / "json").mkdir(exist_ok=True)
        (self.output_dir / "csv").mkdir(exist_ok=True)
        (self.output_dir / "screenshots").mkdir(exist_ok=True)
    
    def save_task_result(self, result: TaskResult) -> Dict[str, str]:
        """Save task result to storage"""
        try:
            saved_files = {}
            
            # Save JSON format
            if self.config.json_format:
                json_file = self._save_json(result)
                saved_files['json'] = json_file
            
            # Save CSV format
            if self.config.csv_format:
                csv_file = self._save_csv(result)
                saved_files['csv'] = csv_file
            
            logger.info(f"Saved task result {result.task_id} to {len(saved_files)} files")
            return saved_files
            
        except Exception as e:
            logger.error(f"Failed to save task result: {e}")
            raise
    
    def _save_json(self, result: TaskResult) -> str:
        """Save result as JSON file"""
        filename = f"task_{result.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / "json" / filename
        
        data = result.to_dict()
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if self.config.pretty_print:
                json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                json.dump(data, f, ensure_ascii=False)
        
        logger.info(f"Saved JSON: {filepath}")
        return str(filepath)
    
    def _save_csv(self, result: TaskResult) -> str:
        """Save result as CSV file"""
        filename = f"task_{result.task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = self.output_dir / "csv" / filename
        
        # Convert results to DataFrame
        if result.results:
            df = pd.DataFrame(result.results)
            
            # Add metadata columns if enabled
            if self.config.include_metadata:
                df['task_id'] = result.task_id
                df['status'] = result.status
                df['instruction'] = result.instruction
                df['timestamp'] = result.timestamp.isoformat()
                df['execution_time'] = result.execution_time
            
            df.to_csv(filepath, index=False, encoding='utf-8')
        else:
            # Create empty CSV with headers
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['task_id', 'status', 'instruction', 'timestamp', 'execution_time'])
                writer.writerow([
                    result.task_id,
                    result.status,
                    result.instruction,
                    result.timestamp.isoformat(),
                    result.execution_time
                ])
        
        logger.info(f"Saved CSV: {filepath}")
        return str(filepath)
    
    def load_task_result(self, task_id: str) -> Optional[TaskResult]:
        """Load task result by ID"""
        try:
            # Look for JSON files with this task_id
            json_dir = self.output_dir / "json"
            for file_path in json_dir.glob(f"task_{task_id}_*.json"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Convert back to TaskResult
                result = TaskResult(
                    task_id=data['task_id'],
                    status=data['status'],
                    instruction=data['instruction'],
                    results=data['results'],
                    metadata=data['metadata'],
                    timestamp=datetime.fromisoformat(data['timestamp']),
                    execution_time=data['execution_time'],
                    error_message=data.get('error_message')
                )
                
                return result
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to load task result {task_id}: {e}")
            return None
    
    def list_task_results(self) -> List[Dict[str, Any]]:
        """List all saved task results"""
        try:
            results = []
            json_dir = self.output_dir / "json"
            
            for file_path in json_dir.glob("task_*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    results.append({
                        'task_id': data['task_id'],
                        'status': data['status'],
                        'instruction': data['instruction'],
                        'timestamp': data['timestamp'],
                        'execution_time': data['execution_time'],
                        'result_count': len(data['results']),
                        'file_path': str(file_path)
                    })
                except Exception as e:
                    logger.warning(f"Failed to read {file_path}: {e}")
                    continue
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to list task results: {e}")
            return []
    
    def export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Export data to CSV file"""
        try:
            filepath = self.output_dir / "csv" / filename
            
            if not data:
                # Create empty CSV
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['No data available'])
            else:
                df = pd.DataFrame(data)
                df.to_csv(filepath, index=False, encoding='utf-8')
            
            logger.info(f"Exported CSV: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export CSV: {e}")
            raise
    
    def export_to_json(self, data: List[Dict[str, Any]], filename: str) -> str:
        """Export data to JSON file"""
        try:
            filepath = self.output_dir / "json" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                if self.config.pretty_print:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            logger.info(f"Exported JSON: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to export JSON: {e}")
            raise
    
    def create_summary_report(self, task_results: List[TaskResult]) -> str:
        """Create a summary report of multiple task results"""
        try:
            summary = {
                'total_tasks': len(task_results),
                'successful_tasks': len([r for r in task_results if r.status == 'success']),
                'failed_tasks': len([r for r in task_results if r.status == 'error']),
                'total_execution_time': sum(r.execution_time for r in task_results),
                'average_execution_time': sum(r.execution_time for r in task_results) / len(task_results) if task_results else 0,
                'tasks': [
                    {
                        'task_id': r.task_id,
                        'status': r.status,
                        'instruction': r.instruction,
                        'result_count': len(r.results),
                        'execution_time': r.execution_time,
                        'timestamp': r.timestamp.isoformat()
                    }
                    for r in task_results
                ]
            }
            
            filename = f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = self.output_dir / "json" / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Created summary report: {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to create summary report: {e}")
            raise
    
    def cleanup_old_files(self, days: int = 30):
        """Clean up files older than specified days"""
        try:
            cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
            cleaned_count = 0
            
            for subdir in ['json', 'csv', 'screenshots']:
                dir_path = self.output_dir / subdir
                if dir_path.exists():
                    for file_path in dir_path.iterdir():
                        if file_path.is_file() and file_path.stat().st_mtime < cutoff_date:
                            file_path.unlink()
                            cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old files: {e}")
            return 0


class StorageFactory:
    """Factory for creating storage instances"""
    
    @staticmethod
    def create_storage(config: Optional[ExportConfig] = None) -> DataStorage:
        """Create a storage instance"""
        return DataStorage(config)


# Example usage
if __name__ == "__main__":
    # Test the storage system
    storage = StorageFactory.create_storage()
    
    # Create a sample task result
    result = TaskResult(
        task_id="test_001",
        status="success",
        instruction="search laptops under 50000",
        results=[
            {"title": "Laptop 1", "price": "₹45,000", "url": "https://example.com/1"},
            {"title": "Laptop 2", "price": "₹42,000", "url": "https://example.com/2"}
        ],
        metadata={"browser": "chromium", "headless": True},
        timestamp=datetime.now(),
        execution_time=15.5
    )
    
    # Save the result
    saved_files = storage.save_task_result(result)
    print(f"Saved files: {saved_files}")
    
    # Load the result
    loaded_result = storage.load_task_result("test_001")
    if loaded_result:
        print(f"Loaded result: {loaded_result.task_id} - {loaded_result.status}")
    
    # List all results
    all_results = storage.list_task_results()
    print(f"Total results: {len(all_results)}")
