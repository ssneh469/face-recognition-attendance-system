#!/usr/bin/env python3
"""
Face Recognition System - Flask Application
Startup Script

This script provides an easy way to run the Face Recognition System.
It handles basic configuration and starts the Flask development server.
"""

import os
import sys
from app import app, db

def main():
    """Main function to start the application"""
    
    print("=" * 60)
    print("🚀 Face Recognition System - Flask Version")
    print("=" * 60)
    
    # Check if we're in the right directory
    if not os.path.exists('app.py'):
        print("❌ Error: app.py not found!")
        print("Please run this script from the 'Face Recognition Flask' directory.")
        sys.exit(1)
    
    # Create database tables
    try:
        with app.app_context():
            db.create_all()
            print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Warning: Database initialization failed: {e}")
        print("The application will continue, but some features may not work.")
    
    # Check for required directories
    required_dirs = ['static', 'static/css', 'static/js', 'static/uploads', 'templates']
    for directory in required_dirs:
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            print(f"📁 Created directory: {directory}")
    
    # Display startup information
    print("\n📋 System Information:")
    print(f"   • Flask Version: {app.config.get('FLASK_VERSION', 'Unknown')}")
    print(f"   • Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Unknown')}")
    print(f"   • Upload Folder: {app.config.get('UPLOAD_FOLDER', 'Unknown')}")
    print(f"   • Debug Mode: {app.config.get('DEBUG', False)}")
    
    print("\n🔐 Default Login Credentials:")
    print("   • Email: admin@admin.com")
    print("   • Password: admin123")
    
    print("\n🌐 Access Information:")
    print("   • Local URL: http://localhost:5000")
    print("   • Network URL: http://0.0.0.0:5000")
    
    print("\n⚠️  Important Notes:")
    print("   • Ensure your webcam is accessible")
    print("   • Allow camera permissions in your browser")
    print("   • For production use, change the secret key")
    
    print("\n" + "=" * 60)
    print("🎯 Starting Face Recognition System...")
    print("=" * 60)
    
    try:
        # Start the application
        app.run(
            debug=True,
            host='0.0.0.0',
            port=5000,
            use_reloader=True
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Application stopped by user")
        print("Thank you for using Face Recognition System!")
    except Exception as e:
        print(f"\n❌ Error starting application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()

