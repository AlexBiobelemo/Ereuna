import streamlit as st
import os
import logging
from utils.research_generator import ResearchGenerator
from utils.notes_manager import NotesManager
from utils.pdf_generator import PdfGenerator
from utils.powerpoint_generator import PowerpointGenerator
from utils.session_state_manager import SessionStateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def app():
    st.set_page_config(page_title="Research Report Generator", layout="wide")
    
    # CRITICAL: Initialize session state first
    SessionStateManager.initialize_state()
    
    st.title("🔬 Automated Research Report Generator")
    st.markdown("Generate comprehensive research reports with AI-powered insights")

    # --- Configuration ---
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
    except Exception as e:
        st.error("⚠️ Error: GEMINI_API_KEY not found in .streamlit/secrets.toml")
        st.info("Please add your Gemini API key to .streamlit/secrets.toml or enter it below:")
        api_key = st.text_input("Enter Gemini API Key:", type="password")
        if not api_key:
            return

    # --- User Input ---
    st.subheader("📝 Research Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        topic = st.text_input(
            "Enter the research topic:",
            value=SessionStateManager.get_value('current_topic', 'Impact of AI on Education'),
            help="Main topic for your research report"
        )
        
        keywords_input = st.text_input(
            "Enter keywords (comma-separated):",
            value=SessionStateManager.get_value('current_keywords', 
                  'Artificial Intelligence, Learning, Teaching, Future of Education'),
            help="Keywords to guide the research focus"
        )
    
    with col2:
        research_questions_input = st.text_area(
            "Enter research questions (comma-separated):",
            value=SessionStateManager.get_value('current_questions',
                  'How does AI personalize learning?, What are the ethical implications of AI in education?'),
            help="Specific questions to address in the research",
            height=100
        )

    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    research_questions = [q.strip() for q in research_questions_input.split(',') if q.strip()]

    # --- Generate Button ---
    st.divider()
    
    col_btn1, col_btn2, col_btn3 = st.columns([2, 1, 1])
    
    with col_btn1:
        generate_button = st.button(
            "🚀 Generate Research Report",
            type="primary",
            disabled=SessionStateManager.is_generation_in_progress(),
            use_container_width=True
        )
    
    with col_btn2:
        if SessionStateManager.get_value('research_generated', False):
            if st.button("🔄 Start New Research", use_container_width=True):
                SessionStateManager.clear_research_data()
                st.rerun()
    
    with col_btn3:
        if SessionStateManager.get_value('research_generated', False):
            with st.expander("📊 Debug Info"):
                st.json(SessionStateManager.debug_session_state())

    # --- Generation Process ---
    if generate_button:
        if not topic or not keywords or not research_questions:
            st.warning("⚠️ Please fill in all fields to generate the report.")
            return

        try:
            SessionStateManager.set_generation_in_progress(True)
            st.info(f"🔍 Starting research on: **{topic}**...")

            # --- Research Generation ---
            with st.spinner("🤖 Generating research report sections..."):
                research_gen = ResearchGenerator(
                    topic=topic,
                    keywords=keywords,
                    research_questions=research_questions,
                    api_key=api_key,
                    system_prompt="You are a helpful research assistant. Provide detailed and well-structured information."
                )
                sections_content = research_gen.generate_report()
            
            # Check for errors in sections
            error_sections = [name for name, content in sections_content.items() 
                            if content.startswith("Error")]
            
            if error_sections:
                st.warning(f"⚠️ Some sections failed to generate: {', '.join(error_sections)}")
            else:
                st.success("✅ Research report sections generated successfully!")
            
            # CRITICAL: Store research data in session state immediately
            SessionStateManager.store_research_data(sections_content, topic, keywords_input, research_questions_input)

            # --- Notes Management ---
            try:
                notes_filepath = f"{topic.replace(' ', '_')}_research_notes.txt"
                notes_manager = NotesManager(filepath=notes_filepath)
                full_report_text = "\n\n".join([f"## {title}\n{content}" for title, content in sections_content.items()])
                notes_manager.update_notes(full_report_text)
                
                if notes_manager.save_notes():
                    st.success(f"📝 Research notes saved to {notes_filepath}")
                    SessionStateManager.store_notes(full_report_text)
                else:
                    st.warning("⚠️ Failed to save research notes")
            except Exception as e:
                st.error(f"❌ Error saving notes: {str(e)}")
                logging.error(f"Notes saving error: {e}")

        except Exception as e:
            st.error(f"❌ Error during research generation: {str(e)}")
            logging.error(f"Research generation error: {e}")
            SessionStateManager.set_value('error_message', str(e))
        finally:
            SessionStateManager.set_generation_in_progress(False)

    # --- Display Generated Research ---
    if SessionStateManager.get_value('research_generated', False):
        st.divider()
        st.subheader("📚 Generated Research Report")
        
        sections_content = SessionStateManager.get_value('research_sections', {})
        
        # Display sections in tabs
        if sections_content:
            tabs = st.tabs(list(sections_content.keys()))
            for tab, (section_name, content) in zip(tabs, sections_content.items()):
                with tab:
                    st.markdown(content)
        
        # --- Export Options ---
        st.divider()
        st.subheader("📥 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        # --- PDF Generation ---
        with col1:
            st.markdown("### 📄 PDF Report")
            if st.button("Generate PDF", key="gen_pdf_btn", use_container_width=True):
                try:
                    with st.spinner("Generating PDF report..."):
                        topic = SessionStateManager.get_value('current_topic')
                        pdf_output_path = f"{topic.replace(' ', '_')}_research_report.pdf"
                        
                        pdf_gen = PdfGenerator(topic=topic)
                        pdf_gen.generate_pdf_report(sections_content, output_path=pdf_output_path)
                        
                        # CRITICAL: Read file and store in session state
                        with open(pdf_output_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        SessionStateManager.store_file_data('pdf', pdf_output_path, pdf_bytes)
                        st.success("✅ PDF report generated!")
                except Exception as e:
                    st.error(f"❌ PDF generation failed: {str(e)}")
                    logging.error(f"PDF generation error: {e}")
            
            # Show download button if PDF exists in session state
            if SessionStateManager.is_file_generated('pdf'):
                pdf_bytes = SessionStateManager.get_file_bytes('pdf')
                if pdf_bytes:
                    topic = SessionStateManager.get_value('current_topic')
                    st.download_button(
                        label="📥 Download PDF Report",
                        data=pdf_bytes,
                        file_name=f"{topic.replace(' ', '_')}_research_report.pdf",
                        mime="application/pdf",
                        key="download_pdf_btn",
                        use_container_width=True
                    )
        
        # --- PowerPoint Generation ---
        with col2:
            st.markdown("### 📊 PowerPoint")
            if st.button("Generate PowerPoint", key="gen_pptx_btn", use_container_width=True):
                try:
                    with st.spinner("Generating PowerPoint presentation..."):
                        topic = SessionStateManager.get_value('current_topic')
                        
                        # Prepare slides data
                        slides_data = []
                        # Add title slide
                        slides_data.append({
                            "title": topic,
                            "bullets": ["Comprehensive Research Report", f"Generated on {st.session_state.get('generation_date', 'today')}"]
                        })
                        
                        # Add content slides
                        for title, content in sections_content.items():
                            bullets = [line.strip() for line in content.split('\n') 
                                     if line.strip() and len(line.strip()) > 10][:8]
                            if bullets:
                                slides_data.append({"title": title, "bullets": bullets})
                        
                        pptx_output_path = f"{topic.replace(' ', '_')}_research_presentation.pptx"
                        powerpoint_gen = PowerpointGenerator(topic=topic)
                        powerpoint_gen.generate_powerpoint(slides_data, output_path=pptx_output_path)
                        
                        # CRITICAL: Read file and store in session state
                        with open(pptx_output_path, "rb") as f:
                            pptx_bytes = f.read()
                        
                        SessionStateManager.store_file_data('pptx', pptx_output_path, pptx_bytes)
                        st.success("✅ PowerPoint presentation generated!")
                except Exception as e:
                    st.error(f"❌ PowerPoint generation failed: {str(e)}")
                    logging.error(f"PowerPoint generation error: {e}")
            
            # Show download button if PPTX exists in session state
            if SessionStateManager.is_file_generated('pptx'):
                pptx_bytes = SessionStateManager.get_file_bytes('pptx')
                if pptx_bytes:
                    topic = SessionStateManager.get_value('current_topic')
                    st.download_button(
                        label="📥 Download PowerPoint",
                        data=pptx_bytes,
                        file_name=f"{topic.replace(' ', '_')}_research_presentation.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        key="download_pptx_btn",
                        use_container_width=True
                    )
        
        # --- Notes/Text Export ---
        with col3:
            st.markdown("### 📝 Text Notes")
            if st.button("Generate Text File", key="gen_txt_btn", use_container_width=True):
                try:
                    with st.spinner("Generating text file..."):
                        topic = SessionStateManager.get_value('current_topic')
                        notes_content = SessionStateManager.get_notes()
                        
                        if not notes_content:
                            notes_content = "\n\n".join([f"## {title}\n{content}" 
                                                        for title, content in sections_content.items()])
                        
                        txt_bytes = notes_content.encode('utf-8')
                        SessionStateManager.store_file_data('docx', 'notes.txt', txt_bytes)
                        st.success("✅ Text file ready!")
                except Exception as e:
                    st.error(f"❌ Text file generation failed: {str(e)}")
                    logging.error(f"Text generation error: {e}")
            
            # Show download button if text exists
            if SessionStateManager.is_file_generated('docx'):
                txt_bytes = SessionStateManager.get_file_bytes('docx')
                if txt_bytes:
                    topic = SessionStateManager.get_value('current_topic')
                    st.download_button(
                        label="📥 Download Text File",
                        data=txt_bytes,
                        file_name=f"{topic.replace(' ', '_')}_research_notes.txt",
                        mime="text/plain",
                        key="download_txt_btn",
                        use_container_width=True
                    )
        
        # Success message
        if (SessionStateManager.is_file_generated('pdf') or 
            SessionStateManager.is_file_generated('pptx') or 
            SessionStateManager.is_file_generated('docx')):
            st.balloons()

    # --- Display Errors ---
    error_msg = SessionStateManager.get_value('error_message')
    if error_msg:
        st.error(f"❌ Error: {error_msg}")
        if st.button("Clear Error"):
            SessionStateManager.clear_error()
            st.rerun()

    # --- Footer ---
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>🤖 Powered by Google Gemini AI | Built with Streamlit</p>
        <p style='font-size: 0.8em;'>Generate professional research reports with AI assistance</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    app()
