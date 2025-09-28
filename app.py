"""
Flask web application for the Local AI Agent
"""

import os
import json
import asyncio
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
import uuid

from src.agent.orchestrator import OrchestratorFactory
from src.agent.browser_controller import BrowserConfig
from src.utils.storage import ExportConfig
from src.memory.session_memory import MemoryFactory

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Global orchestrator instance
orchestrator = None

def get_orchestrator():
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        # Configure components with proper timeout
        browser_config = BrowserConfig(
            headless=os.getenv('BROWSER_HEADLESS', 'true').lower() == 'true',
            browser_type=os.getenv('BROWSER_TYPE', 'chromium'),
            timeout=30000  # 30 seconds timeout
        )
        
        storage_config = ExportConfig(
            output_dir=os.getenv('OUTPUT_DIR', 'exports'),
            json_format=True,
            csv_format=True
        )
        
        memory = MemoryFactory.create_memory(
            persist_to_disk=os.getenv('MEMORY_PERSIST', 'true').lower() == 'true'
        )
        
        orchestrator = OrchestratorFactory.create_orchestrator(
            browser_config=browser_config,
            storage_config=storage_config,
            memory=memory
        )
    
    return orchestrator


@app.route('/')
def index():
    """Main web interface"""
    return render_template('index.html')


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0'
    })


@app.route('/run', methods=['POST'])
def run_task():
    """Execute a task from natural language instruction"""
    try:
        data = request.get_json()
        if not data or 'instruction' not in data:
            raise BadRequest('Instruction is required')
        
        instruction = data['instruction'].strip()
        if not instruction:
            raise BadRequest('Instruction cannot be empty')
        
        # Get task ID if provided
        task_id = data.get('task_id', str(uuid.uuid4()))
        
        logger.info(f"Received task request: {task_id} - {instruction}")
        
        # Execute task asynchronously
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            result = loop.run_until_complete(
                get_orchestrator().execute(instruction, task_id)
            )
        finally:
            loop.close()
        
        # Prepare response
        response = {
            'task_id': result.task_id,
            'status': result.status,
            'instruction': result.instruction,
            'results': result.results,
            'execution_time': result.execution_time,
            'error_message': result.error_message,
            'logs': result.logs,
            'metadata': result.metadata
        }
        
        logger.info(f"Task {task_id} completed with status: {result.status}")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 500


@app.route('/results/<task_id>')
def get_results(task_id):
    """Get results for a specific task"""
    try:
        orchestrator = get_orchestrator()
        task_result = orchestrator.storage.load_task_result(task_id)
        
        if not task_result:
            return jsonify({'error': 'Task not found'}), 404
        
        return jsonify({
            'task_id': task_result.task_id,
            'status': task_result.status,
            'instruction': task_result.instruction,
            'results': task_result.results,
            'metadata': task_result.metadata,
            'timestamp': task_result.timestamp.isoformat(),
            'execution_time': task_result.execution_time
        })
        
    except Exception as e:
        logger.error(f"Failed to get results for {task_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/export/<task_id>/csv')
def export_csv(task_id):
    """Export task results as CSV"""
    try:
        orchestrator = get_orchestrator()
        task_result = orchestrator.storage.load_task_result(task_id)
        
        if not task_result:
            return jsonify({'error': 'Task not found'}), 404
        
        # Export to CSV
        filename = f"task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = orchestrator.storage.export_to_csv(task_result.results, filename)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Failed to export CSV for {task_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/export/<task_id>/json')
def export_json(task_id):
    """Export task results as JSON"""
    try:
        orchestrator = get_orchestrator()
        task_result = orchestrator.storage.load_task_result(task_id)
        
        if not task_result:
            return jsonify({'error': 'Task not found'}), 404
        
        # Export to JSON
        filename = f"task_{task_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = orchestrator.storage.export_to_json(task_result.results, filename)
        
        return send_file(filepath, as_attachment=True, download_name=filename)
        
    except Exception as e:
        logger.error(f"Failed to export JSON for {task_id}: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/history')
def get_history():
    """Get task execution history"""
    try:
        orchestrator = get_orchestrator()
        history = orchestrator.get_task_history()
        return jsonify(history)
        
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/stats')
def get_stats():
    """Get session statistics"""
    try:
        orchestrator = get_orchestrator()
        stats = orchestrator.get_session_stats()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get stats: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/memory/clear', methods=['POST'])
def clear_memory():
    """Clear session memory"""
    try:
        orchestrator = get_orchestrator()
        orchestrator.clear_memory()
        return jsonify({'message': 'Memory cleared successfully'})
        
    except Exception as e:
        logger.error(f"Failed to clear memory: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/memory/export')
def export_memory():
    """Export session memory"""
    try:
        orchestrator = get_orchestrator()
        filepath = orchestrator.memory.export_memories()
        
        if filepath:
            return send_file(filepath, as_attachment=True)
        else:
            return jsonify({'error': 'Failed to export memory'}), 500
        
    except Exception as e:
        logger.error(f"Failed to export memory: {e}")
        return jsonify({'error': str(e)}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the app
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
