import streamlit as st
import os
import logging
from utils.research_generator import ResearchGenerator
from utils.notes_manager import NotesManager
from utils.pdf_generator import PdfGenerator
from utils.powerpoint_generator import PowerpointGenerator
from utils.session_state_manager import SessionStateManager
from utils.citation_manager import CitationManager # Import CitationManager
from utils.content_analyzer import ContentAnalyzer # Import ContentAnalyzer
from utils.template_manager import TemplateManager # Import TemplateManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def app():
    st.set_page_config(page_title="Research Report Generator", layout="wide")
    
    # CRITICAL: Initialize session state first
    SessionStateManager.initialize_state()
    

    st.title("🔬 Automated Research Report Generator")
    st.markdown("Generate comprehensive research reports with AI-powered insights")

    # Initialize TemplateManager
    template_manager = TemplateManager()
    template_names = ["None"] + template_manager.get_template_names()

    # --- Configuration ---
    st.subheader("⚙️ Configuration")

    # Template selection
    selected_template_name = st.selectbox(
        "Choose a Research Template:",
        template_names,
        index=0,
        help="Select a pre-built template to guide your research structure and tone."
    )

    current_template = None
    if selected_template_name != "None":
        current_template = template_manager.get_template(selected_template_name)
        if current_template:
            st.info(f"Template '{current_template['name']}' selected: {current_template['description']}")
            # Display template details in an expander
            with st.expander(f"Details for {current_template['name']}"):
                st.json(current_template)

    # Internal API Key and Model Management
    api_keys = {
        "gemini": st.secrets.get("GEMINI_API_KEY", ""),
        "gpt": st.secrets.get("OPENAI_API_KEY", ""),
        "claude": st.secrets.get("ANTHROPIC_API_KEY", "")
    }
    
    # Default model name
    selected_model_name = "gemini-2.5-flash" 

    # --- User Input ---
    st.subheader("📝 Research Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Apply template topic if available
        default_topic = SessionStateManager.get_value('current_topic', 'Impact of AI on Education')
        if current_template and current_template.get("default_topic"):
            default_topic = current_template["default_topic"]

        topic = st.text_input(
            "Enter the research topic:",
            value=default_topic,
            help="Main topic for your research report"
        )
        
        # Apply template keywords if available
        default_keywords = SessionStateManager.get_value('current_keywords', 
                  'Artificial Intelligence, Learning, Teaching, Future of Education')
        if current_template and current_template.get("keywords_suffix"):
            default_keywords = f"{default_keywords}, {current_template['keywords_suffix']}"

        keywords_input = st.text_input(
            "Enter keywords (comma-separated):",
            value=default_keywords,
            help="Keywords to guide the research focus"
        )
    
    with col2:
        # Apply template research questions if available
        default_questions = SessionStateManager.get_value('current_questions',
                  'How does AI personalize learning?, What are the ethical implications of AI in education?')
        if current_template and current_template.get("questions_prefix"):
            default_questions = f"{current_template['questions_prefix']}, {default_questions}"

        research_questions_input = st.text_area(
            "Enter research questions (comma-separated):",
            value=default_questions,
            help="Specific questions to address in the research",
            height=100
        )

    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    research_questions = [q.strip() for q in research_questions_input.split(',') if q.strip()]

    # Determine system prompt and sections based on template
    system_prompt_to_use = "You are a helpful research assistant. Provide detailed and well-structured information."
    sections_to_generate = ["Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion"]

    if current_template:
        system_prompt_to_use = current_template.get("system_prompt", system_prompt_to_use)
        sections_to_generate = current_template.get("sections", sections_to_generate)

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
    
    # Removed Debug Info as per user request
    # with col_btn3:
    #     if SessionStateManager.get_value('research_generated', False):
    #         with st.expander("📊 Debug Info"):
    #             st.json(SessionStateManager.debug_session_state())

    # --- Generation Process ---
    if generate_button:
        if not topic or not keywords or not research_questions:
            st.warning("⚠️ Please fill in all fields to generate the report.")
            return

        try:
            SessionStateManager.set_generation_in_progress(True)
            st.info(f"🔍 Starting research on: **{topic}** using **{selected_model_name}** with template **{selected_template_name}**...")

            # --- Research Generation ---
            with st.spinner(f"🤖 Generating research report sections using {selected_model_name}..."):
                research_gen = ResearchGenerator(
                    topic=topic,
                    keywords=keywords,
                    research_questions=research_questions,
                    api_keys=api_keys,
                    system_prompt=system_prompt_to_use,
                    model_name=selected_model_name
                )
                
                # Generate sections based on the template
                sections_content = {}
                for section_name in sections_to_generate:
                    sections_content[section_name] = research_gen.generate_section(section_name)

            # Check for errors in sections
            error_sections = [name for name, content in sections_content.items() 
                            if content.startswith("Error")]
            
            if error_sections:
                st.warning(f"⚠️ Some sections failed to generate: {', '.join(error_sections)}")
            else:
                st.success("✅ Research report sections generated successfully!")
            
            # CRITICAL: Store research data in session state immediately
            SessionStateManager.store_research_data(sections_content, topic, keywords_input, research_questions_input, selected_model_name)

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
        
        # --- Quality & Intelligence Features ---
        st.divider()
        st.subheader("✨ Quality & Intelligence")

        # Smart Summarization
        if SessionStateManager.get_value('research_generated', False):
            if st.button("Generate Executive Summary", key="gen_summary_btn", use_container_width=True):
                try:
                    SessionStateManager.set_generation_in_progress(True)
                    with st.spinner(f"🤖 Generating executive summary using {selected_model_name}..."):
                        full_report_content = "\n\n".join([f"## {title}\n{content}" for title, content in sections_content.items()])
                        
                        research_gen = ResearchGenerator(
                            topic=topic,
                            keywords=keywords,
                            research_questions=research_questions,
                            api_keys=api_keys,
                            system_prompt="You are a helpful research assistant. Provide detailed and well-structured information.",
                            model_name=selected_model_name
                        )
                        executive_summary = research_gen.generate_summary(full_report_content)
                        SessionStateManager.set_value('executive_summary', executive_summary)
                        st.success("✅ Executive summary generated!")
                except Exception as e:
                    st.error(f"❌ Error generating executive summary: {str(e)}")
                    logging.error(f"Executive summary generation error: {e}")
                finally:
                    SessionStateManager.set_generation_in_progress(False)
            
            if SessionStateManager.get_value('executive_summary'):
                with st.expander("Executive Summary"):
                    st.markdown(SessionStateManager.get_value('executive_summary'))
            

        # --- Enhanced Research Capabilities ---
        st.divider()
        st.subheader("🔍 Enhanced Research Capabilities")

        # Web Scraping Integration
        if st.button("Perform Web Research (Academic Sources)", key="web_research_btn", use_container_width=True):
            try:
                SessionStateManager.set_generation_in_progress(True)
                with st.spinner(f"🌐 Searching academic sources for '{topic}'..."):
                    research_gen = ResearchGenerator(
                        topic=topic,
                        keywords=keywords,
                        research_questions=research_questions,
                        api_keys=api_keys,
                        system_prompt="You are a helpful research assistant. Provide detailed and well-structured information.",
                        model_name=selected_model_name
                    )
                    search_query = f"{topic} {keywords_input} academic papers"
                    academic_sources = research_gen.perform_web_research(search_query, num_sources=5)
                    SessionStateManager.set_value('academic_sources', academic_sources)
                    if academic_sources:
                        st.success(f"✅ Found {len(academic_sources)} academic sources!")
                        st.info("🌐 Note: Web scraping is currently simulated with dummy URLs. For real-world data, integrate with actual academic search APIs and web content.")
                    else:
                        st.warning("⚠️ No academic sources found for your query.")
            except Exception as e:
                st.error(f"❌ Error during web research: {str(e)}")
                logging.error(f"Web research error: {e}")
            finally:
                SessionStateManager.set_generation_in_progress(False)
        
        if SessionStateManager.get_value('academic_sources'):
            st.markdown("### Found Academic Sources:")
            for i, source in enumerate(SessionStateManager.get_value('academic_sources')):
                st.markdown(f"{i+1}. [{source['title']}]({source['url']})")
                if st.button(f"Scrape Content from Source {i+1}", key=f"scrape_source_{i+1}_btn"):
                    try:
                        SessionStateManager.set_generation_in_progress(True)
                        with st.spinner(f"Scraping content from {source['url']}..."):
                            research_gen = ResearchGenerator(
                                topic=topic,
                                keywords=keywords,
                                research_questions=research_questions,
                                api_keys=api_keys,
                                system_prompt="You are a helpful research assistant. Provide detailed and well-structured information.",
                                model_name=selected_model_name
                            )
                            scraped_content = research_gen.scrape_source_content(source['url'])
                            if scraped_content:
                                SessionStateManager.set_value(f'scraped_content_{i}', scraped_content)
                                st.success(f"✅ Content scraped from {source['url']}!")
                                st.info("🌐 Note: Content scraping from dummy URLs is simulated. For real-world data, ensure URLs are valid and accessible.")
                                with st.expander(f"Scraped Content from {source['title']}"):
                                    st.text_area("Content", scraped_content, height=300)
                            else:
                                st.warning(f"⚠️ Failed to scrape content from {source['url']}.")
                    except Exception as e:
                        st.error(f"❌ Error scraping content: {str(e)}")
                        logging.error(f"Scraping error: {e}")
                    finally:
                        SessionStateManager.set_generation_in_progress(False)
        
        # Citation Management
        if SessionStateManager.get_value('academic_sources'):
            st.markdown("---")
            st.markdown("### 📚 Citation Management")
            citation_style = st.selectbox(
                "Choose Citation Style:",
                ["APA", "MLA", "Chicago"],
                index=0,
                help="Select the citation style for your bibliography."
            )
            if st.button("Generate Bibliography", key="gen_bib_btn", use_container_width=True):
                try:
                    citation_manager = CitationManager()
                    # For demonstration, we'll use dummy data for author, year, publisher
                    # In a real scenario, this would be extracted during web scraping or from metadata
                    formatted_sources = []
                    for source in SessionStateManager.get_value('academic_sources'):
                        # Dummy data for demonstration
                        formatted_sources.append({
                            "title": source['title'],
                            "url": source['url'],
                            "author": "AI Research Bot", 
                            "year": "2025",
                            "publisher": "Automated Research Press",
                            "container": "Online Article" # For MLA
                        })
                    
                    bibliography = citation_manager.generate_bibliography(formatted_sources, style=citation_style)
                    SessionStateManager.set_value('bibliography', bibliography)
                    st.success(f"✅ Bibliography generated in {citation_style} style!")
                    st.info("📝 Note: Citation details (author, year, publisher) are currently dummy data. For real-world accuracy, these would be extracted from actual source metadata.")
                except Exception as e:
                    st.error(f"❌ Error generating bibliography: {str(e)}")
                    logging.error(f"Bibliography generation error: {e}")
            
            if SessionStateManager.get_value('bibliography'):
                with st.expander("Generated Bibliography"):
                    st.markdown(SessionStateManager.get_value('bibliography'))

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
                        
                        # Add executive summary slide if available
                        executive_summary = SessionStateManager.get_value('executive_summary')
                        if executive_summary:
                            summary_bullets = [line.strip() for line in executive_summary.split('\n') 
                                               if line.strip() and len(line.strip()) > 10][:8]
                            if summary_bullets:
                                slides_data.append({"title": "Executive Summary", "bullets": summary_bullets})

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
