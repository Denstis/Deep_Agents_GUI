#!/usr/bin/env python3
"""
DeepAgents GUI - Main Application Entry Point
Real LangChain/LangGraph integration with multi-agent support.
"""
import sys
import os

# Add workspace to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    """Main entry point"""
    print("=" * 60)
    print("DeepAgents GUI - Starting...")
    print("=" * 60)
    
    # Check dependencies
    try:
        import customtkinter
        print("✓ CustomTkinter loaded")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Install with: pip install -r requirements.txt")
        return 1
    
    try:
        from langchain_openai import ChatOpenAI
        print("✓ LangChain loaded")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Install with: pip install -r requirements.txt")
        return 1
    
    try:
        from langgraph.graph import StateGraph
        print("✓ LangGraph loaded")
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        print("Install with: pip install -r requirements.txt")
        return 1
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠ Warning: OPENAI_API_KEY not set in .env file")
        print("  Some features may not work without an API key")
        print("  Copy .env.example to .env and add your key")
    else:
        print("✓ OpenAI API key found")
    
    print("=" * 60)
    
    # Import and run GUI
    try:
        from gui.main_window import DeepAgentsGUI
        print("✓ Loading GUI...")
        
        # Initialize GUI in the main thread
        app = DeepAgentsGUI()
        
        # Update stats after a short delay to ensure UI is ready
        def finalize_init():
            try:
                app._update_stats()
                print("✓ GUI initialized successfully")
                print("✓ Starting main event loop...")
            except Exception as e:
                print(f"⚠ Warning during finalization: {e}")
        
        app.after(1000, finalize_init)
        app.mainloop()
        
        return 0
        
    except Exception as e:
        print(f"✗ Failed to start GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
