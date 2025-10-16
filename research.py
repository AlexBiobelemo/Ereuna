import streamlit as st
import os
import logging
from utils.research_generator import ResearchGenerator
from utils.notes_manager import NotesManager
from utils.docx_generator import DocxGenerator
from utils.session_state_manager import SessionStateManager
from utils.content_analyzer import ContentAnalyzer
from utils.template_manager import TemplateManager
from utils.chat_manager import ChatManager
from utils.config_manager import ConfigManager # Import ConfigManager
from utils.prompt_manager import PromptManager # Import PromptManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def app():
    st.set_page_config(page_title="Research Report Generator", layout="wide")
    
    # CRITICAL: Initialize session state first
    SessionStateManager.initialize_state()
    
    st.title("🔬 Automated Research Report Generator")
    st.markdown("Generate comprehensive research reports with AI-powered insights")

    # Initialize ConfigManager, TemplateManager, and PromptManager
    config_manager = ConfigManager() # Initialize ConfigManager
    template_manager = TemplateManager()
    prompt_manager = PromptManager() # Initialize PromptManager
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

    # API Key and Model Management from ConfigManager
    api_keys = config_manager.get_api_keys()
    
    # Model selection
    available_models = config_manager.get_available_models()
    model_display_names = {name: info["display_name"] for name, info in available_models.items()}
    
    # Ensure default model is in the list of available models
    default_model_name = config_manager.get_default_model()
    if default_model_name not in available_models:
        default_model_name = next(iter(available_models.keys()), "gemini-2.5-flash") # Fallback to first available or a hardcoded default

    selected_model_display_name = st.selectbox(
        "Choose an LLM Model:",
        options=list(model_display_names.values()),
        index=list(model_display_names.keys()).index(default_model_name) if default_model_name in model_display_names else 0,
        format_func=lambda x: x,
        help="Select the Large Language Model to power your research."
    )
    
    # Map display name back to model ID
    selected_model_name = next(
        (model_id for model_id, display_name in model_display_names.items() if display_name == selected_model_display_name),
        default_model_name
    )

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
        
        # Add Deep Research checkbox
        deep_research_default = SessionStateManager.get_value('deep_research_enabled', False)
        deep_research_enabled = st.checkbox(
            "Enable Deep Research (more detailed and extensive)",
            value=deep_research_default,
            key="deep_research_checkbox",
            help="If checked, the AI will perform a more in-depth and extensive research process."
        )
        SessionStateManager.set_value('deep_research_enabled', deep_research_enabled)

    keywords = [k.strip() for k in keywords_input.split(',') if k.strip()]
    research_questions = [q.strip() for q in research_questions_input.split(',') if q.strip()]

    # Determine sections to generate based on template or user input
    sections_to_generate = ["Introduction", "Literature Review", "Methodology", "Results", "Discussion", "Conclusion"]
    
    custom_sections_input = ""
    if selected_template_name == "Custom Template":
        st.markdown("---")
        st.subheader("Custom Template Configuration")
        custom_sections_input = st.text_area(
            "Define your custom sections (one per line or comma-separated):",
            value=SessionStateManager.get_value('custom_sections_input', "Introduction\nBackground\nMethodology\nFindings\nConclusion"),
            height=150,
            help="Enter the titles for your desired report sections. Each line or comma-separated value will be a new section."
        )
        SessionStateManager.set_value('custom_sections_input', custom_sections_input)
        
        if custom_sections_input:
            # Split by newline or comma, then clean up
            sections_from_input = [s.strip() for s in custom_sections_input.replace('\n', ',').split(',') if s.strip()]
            if sections_from_input:
                sections_to_generate = sections_from_input
            else:
                st.warning("Please define at least one custom section for the 'Custom Template'.")
                sections_to_generate = [] # Prevent generation with empty sections
        else:
            sections_to_generate = [] # Prevent generation with empty sections

    elif current_template:
        template_sections = current_template.get("sections", sections_to_generate)
        
        # Ensure sections_to_generate is a list of strings
        if isinstance(template_sections, list):
            sections_to_generate = template_sections
        else:
            sections_to_generate = template_sections

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
    
    # --- Generation Process ---
    if generate_button:
        if not topic or not keywords or not research_questions:
            st.warning("⚠️ Please fill in all fields to generate the report.")
            return

        try:
            SessionStateManager.set_generation_in_progress(True)
            st.info(f"🔍 Starting research on: **{topic}** using **{selected_model_name}** with template **{selected_template_name}**...")

            # --- Research Generation ---
            with st.spinner(f"🚀 Starting research generation..."):
                # Create a placeholder for the spinner message
                spinner_message_placeholder = st.empty()
                st.session_state.update_spinner = lambda msg: spinner_message_placeholder.text(f"✨ {msg}")

                research_gen = ResearchGenerator(
                    topic=topic,
                    keywords=keywords,
                    research_questions=research_questions,
                    config_manager=config_manager, # Pass config_manager
                    prompt_manager=prompt_manager, # Pass prompt_manager
                    model_name=selected_model_name,
                    spinner_update_callback=st.session_state.update_spinner
                )
                
                # Generate sections based on the template
                sections_content = {}
                all_previous_content = "" # Initialize for contextual generation

                for section_data in sections_to_generate:
                    section_title = ""
                    if isinstance(section_data, dict) and "title" in section_data:
                        section_title = section_data["title"]
                        generated_content = research_gen.generate_section(section_data, previous_sections_content=all_previous_content)
                    elif isinstance(section_data, str):
                        section_title = section_data
                        generated_content = research_gen.generate_section(section_data, previous_sections_content=all_previous_content)
                    else:
                        logging.warning(f"Skipping invalid section data in template: {section_data}")
                        continue # Skip to next section

                    sections_content[section_title] = generated_content
                    all_previous_content += f"\n\n## {section_title}\n{generated_content}" # Append for next section's context

            # Check for errors in sections
            error_sections = [name for name, content in sections_content.items() 
                            if content.startswith("Error")]
            
            if error_sections:
                st.warning(f"⚠️ Some sections failed to generate: {', '.join(error_sections)}")
            else:
                st.success("✅ Research report sections generated successfully!")
            
            # CRITICAL: Store research data in session state immediately
            SessionStateManager.store_research_data(sections_content, topic, keywords_input, research_questions_input, selected_model_name)

            # Initialize and load research content into ChatManager
            chat_manager = ChatManager(config_manager=config_manager, prompt_manager=prompt_manager, model_name=selected_model_name, research_topic=topic) # Pass config_manager and prompt_manager
            chat_manager.load_research_content(sections_content)
            SessionStateManager.set_value('chat_manager', chat_manager)

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
                    with st.spinner(f"📝 Preparing executive summary..."):
                        # Create a placeholder for the spinner message
                        summary_spinner_message_placeholder = st.empty()
                        st.session_state.update_summary_spinner = lambda msg: summary_spinner_message_placeholder.text(f"📝 {msg}")

                        full_report_content = "\n\n".join([f"## {title}\n{content}" for title, content in sections_content.items()])
                        
                        research_gen = ResearchGenerator(
                            topic=topic,
                            keywords=keywords,
                            research_questions=research_questions,
                            config_manager=config_manager,
                            prompt_manager=prompt_manager,
                            model_name=selected_model_name,
                            spinner_update_callback=st.session_state.update_summary_spinner
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
            
            # Readability Analysis
            if st.button("Analyze Readability", key="analyze_readability_btn", use_container_width=True):
                try:
                    SessionStateManager.set_generation_in_progress(True)
                    with st.spinner("📈 Analyzing readability..."):
                        full_report_content = "\n\n".join([f"## {title}\n{content}" for title, content in sections_content.items()])
                        analyzer = ContentAnalyzer(config_manager=config_manager) # Pass config_manager
                        readability_scores = analyzer.analyze_readability(full_report_content)
                        SessionStateManager.set_value('readability_scores', readability_scores)
                        st.success("✅ Readability analysis complete!")
                except Exception as e:
                    st.error(f"❌ Error analyzing readability: {str(e)}")
                    logging.error(f"Readability analysis error: {e}")
                finally:
                    SessionStateManager.set_generation_in_progress(False)
            
            if SessionStateManager.get_value('readability_scores'):
                with st.expander("Readability Scores"):
                    scores = SessionStateManager.get_value('readability_scores')
                    st.markdown("---")
                    st.markdown("### Readability Metrics:")
                    for metric, value in scores.items():
                        if isinstance(value, dict):
                            st.markdown(f"**{metric.replace('_', ' ').title()}:**")
                            for sub_metric, sub_value in value.items():
                                st.markdown(f"- {sub_metric.replace('_', ' ').title()}: `{sub_value:.2f}`")
                        else:
                            st.markdown(f"- {metric.replace('_', ' ').title()}: `{value:.2f}`")
                    st.markdown("---")

        # --- Export Options ---
        st.divider()
        st.subheader("📥 Export Options")
        
        col1, col2 = st.columns(2)
        
        # --- Notes/Text Export ---
        with col1:
            st.markdown("### 📝 Text Notes")
            # Download Text File
            notes_content = SessionStateManager.get_notes()
            if notes_content:
                topic = SessionStateManager.get_value('current_topic', 'research_notes')
                st.download_button(
                    label="📥 Download Text File",
                    data=notes_content.encode('utf-8'),
                    file_name=f"{topic.replace(' ', '_')}_research_notes.txt",
                    mime="text/plain",
                    key="download_txt_btn",
                    use_container_width=True
                )

            # Live Notes Editor
            st.markdown("### 📝 Live Notes Editor")
            current_notes_content = SessionStateManager.get_notes()
            edited_notes = st.text_area(
                "Live Notes Editor",
                value=current_notes_content,
                height=300,
                key="live_notes_editor",
                on_change=lambda: SessionStateManager.store_notes(st.session_state.live_notes_editor)
            )
            # Ensure session state is updated if text area is edited
            if edited_notes != current_notes_content:
                SessionStateManager.store_notes(edited_notes)
        
        # --- DOCX Generation ---
        with col2:
            st.markdown("### 📄 DOCX Report")
            if st.button("Generate DOCX", key="gen_docx_btn", use_container_width=True):
                try:
                    with st.spinner("📄 Finalizing DOCX report..."):
                        topic = SessionStateManager.get_value('current_topic')
                        sections_content = SessionStateManager.get_value('research_sections', {})
                        
                        docx_output_path = f"{topic.replace(' ', '_')}_research_report.docx"
                        
                        docx_gen = DocxGenerator(topic=topic)
                        docx_gen.generate_docx_report(sections_content, docx_output_path)
                        
                        # CRITICAL: Read file and store in session state
                        with open(docx_output_path, "rb") as f:
                            docx_bytes = f.read()
                        
                        SessionStateManager.store_file_data('docx', docx_output_path, docx_bytes)
                        st.success("✅ DOCX report generated!")
                except Exception as e:
                    st.error(f"❌ DOCX generation failed: {str(e)}")
                    logging.error(f"DOCX generation error: {e}")
            
            # Show download button if DOCX exists in session state
            if SessionStateManager.is_file_generated('docx'):
                docx_bytes = SessionStateManager.get_file_bytes('docx')
                if docx_bytes:
                    topic = SessionStateManager.get_value('current_topic')
                    st.download_button(
                        label="📥 Download DOCX Report",
                        data=docx_bytes,
                        file_name=f"{topic.replace(' ', '_')}_research_report.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key="download_docx_btn",
                        use_container_width=True
                    )

        # Success message
        if (SessionStateManager.is_file_generated('docx') or
            SessionStateManager.is_file_generated('txt')):
            st.balloons()

    # --- Chat Interface ---
    st.divider()
    st.subheader("💬 Research Chatbot")
    st.info("Ask questions about the generated research report. The chatbot will only respond based on the content of the report.")

    if SessionStateManager.get_value('research_generated', False):
        chat_manager = SessionStateManager.get_value('chat_manager')
        if chat_manager is None:
            st.error("Chatbot not initialized. Please regenerate the report.")
            return

        if 'chat_history' not in st.session_state:
            st.session_state.chat_history = []
        
        # Display chat messages from history on app rerun
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Clear chat button
        if st.button("Clear Chat", key="clear_chat_button"):
            chat_manager.clear_chat_history()
            st.session_state.chat_history = [] # Also clear Streamlit's session state chat history
            st.rerun()

        # React to user input
        if prompt := st.chat_input("Ask a question about the research..."):
            # Add user message to chat history
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_manager.generate_chat_response(prompt)
                    st.markdown(response)
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
    else:
        st.warning("Please generate a research report first to enable the chatbot.")

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
        <p>AlexAlagoaBiobelemo</p>
        <p style='font-size: 0.8em;'>Generate professional research reports with AI assistance</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    app()
