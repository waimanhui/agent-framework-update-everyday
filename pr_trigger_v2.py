import asyncio
import sys
import os
import shutil
from copilot import CopilotClient
from copilot.generated.session_events import SessionEventType



async def main():
    client = CopilotClient()
    await client.start()
    
    # Create the PR analyzer skill
    work_dir = os.getcwd()
    skills_dir = "./.copilot_skills/pr-analyzer/SKILL.md"
    
    # Check and create blog folder if not exists
    blog_dir = os.path.join(work_dir, "blog")
    if not os.path.exists(blog_dir):
        os.makedirs(blog_dir)
        print(f"✓ Created blog folder at: {blog_dir}")
    else:
        print(f"✓ Blog folder exists at: {blog_dir}")
    
    # Create session with Claude Sonnet 4.5 and the skill
    session = await client.create_session({
        "model": "claude-sonnet-4.5",
        "streaming": True,
        "skill_directories": [skills_dir]
    })
    
    print(f"✓ Session created with ID: {session.session_id}")
    print("\n" + "="*80)
    print("Starting PR Analysis...")
    print("="*80 + "\n")
    
    # Listen for response chunks
    def handle_event(event):
        if event.type == SessionEventType.ASSISTANT_MESSAGE_DELTA:
            sys.stdout.write(event.data.delta_content)
            sys.stdout.flush()
        if event.type == SessionEventType.SESSION_IDLE:
            print("\n")  # New line when done
    
    session.on(handle_event)
    
    # Send the task to analyze PRs
    prompt = """
Analyze PRs from https://github.com/microsoft/agent-framework merged yesterday， and write a detailed blog post summarizing the changes, including code examples where relevant.
"""
    
    # Increase timeout to 10 minutes for complex web scraping and analysis
    await session.send_and_wait({"prompt": prompt}, timeout=600)
    
    print("\n" + "="*80)
    print("Analysis Complete!")
    print("="*80)
    
    await client.stop()


if __name__ == "__main__":
    asyncio.run(main())