import streamlit as st
import pandas as pd
from PIL import Image
import numpy as np
import random
import time
from datetime import datetime
import uuid
import base64
import io

def computer_Vision():
    st.header("Computer Vision - Damage Assessment")
    
    # Create tabs for different functionalities
    cv_tabs = st.tabs(["Image Upload", "Assessment History", "Settings"])

    with cv_tabs[0]:
        image_upload_tab()
    
    with cv_tabs[1]:
        assessment_history_tab()
    
    with cv_tabs[2]:
        settings_tab()

def image_upload_tab():
    st.subheader("Vehicle Damage Assessment")
    st.caption("Upload vehicle damage images to get AI-powered severity assessment")
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose vehicle damage images", 
        type=['png', 'jpg', 'jpeg', 'webp'],
        accept_multiple_files=True,
        help="Upload clear images of vehicle damage for assessment"
    )
    
    if uploaded_files:
        # Create columns for layout
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Uploaded Images")
            
            # Display uploaded images in a grid
            for i, uploaded_file in enumerate(uploaded_files):
                with st.expander(f"Image {i+1}: {uploaded_file.name}", expanded=True):
                    # Display image
                    image = Image.open(uploaded_file)
                    st.image(image, caption=f"Uploaded: {uploaded_file.name}", use_container_width =True)
                    
                    # Image details
                    img_details = get_image_details(image, uploaded_file)
                    st.json(img_details)
        
        with col2:
            st.subheader("AI Assessment")
            
            # Assessment button
            if st.button("Analyze Damage", type="primary", use_container_width=True):
                assess_damage(uploaded_files)
            
            # Quick stats
            st.metric("Images Uploaded", len(uploaded_files))
            st.metric("Total Size", f"{sum(file.size for file in uploaded_files) / 1024 / 1024:.2f} MB")
    
    # else:
        # Show example when no files uploaded
        # show_example_interface()

def assess_damage(uploaded_files):
    """Simulate damage assessment with severity scoring"""
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    results = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        # Simulate processing time
        status_text.text(f"Analyzing {uploaded_file.name}...")
        time.sleep(0.5)  # Simulate AI processing
        
        # Generate dummy severity assessment
        assessment = generate_dummy_assessment(uploaded_file)
        results.append(assessment)
        
        # Update progress
        progress_bar.progress((i + 1) / len(uploaded_files))
    
    status_text.text("Analysis complete!")
    time.sleep(0.5)
    status_text.empty()
    progress_bar.empty()
    
    # Display results
    display_assessment_results(results)
    
    # Store in session state for history
    if "assessment_history" not in st.session_state:
        st.session_state.assessment_history = []
    
    st.session_state.assessment_history.extend(results)

def generate_dummy_assessment(uploaded_file):
    """Generate dummy damage assessment data"""
    
    # Simulate different damage types and severities
    damage_types = [
        {"type": "Scratch", "severity_range": (10, 40)},
        {"type": "Dent", "severity_range": (20, 60)},
        {"type": "Crack", "severity_range": (30, 70)},
        {"type": "Collision Damage", "severity_range": (50, 90)},
        {"type": "Paint Damage", "severity_range": (15, 45)},
        {"type": "Structural Damage", "severity_range": (70, 95)}
    ]
    
    # Randomly select damage type
    damage = random.choice(damage_types)
    severity_score = random.randint(*damage["severity_range"])
    
    # Generate confidence score
    confidence = random.randint(75, 98)
    
    # Determine severity level
    if severity_score <= 30:
        severity_level = "Minor"
        color = "🟢"
    elif severity_score <= 60:
        severity_level = "Moderate"
        color = "🟡"
    elif severity_score <= 80:
        severity_level = "Severe"
        color = "🟠"
    else:
        severity_level = "Critical"
        color = "🔴"
    
    # Generate repair cost estimate
    base_cost = severity_score * random.randint(8, 15)
    estimated_cost = base_cost + random.randint(-200, 500)
    
    return {
        "id": str(uuid.uuid4())[:8],
        "filename": uploaded_file.name,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "damage_type": damage["type"],
        "severity_score": severity_score,
        "severity_level": severity_level,
        "severity_color": color,
        "confidence": confidence,
        "estimated_cost": max(100, estimated_cost),  # Minimum cost of 100
        "recommended_action": get_recommended_action(severity_score),
        "processing_time": round(random.uniform(0.5, 2.5), 2)
    }

def get_recommended_action(severity_score):
    """Get recommended action based on severity score"""
    if severity_score <= 30:
        return "Minor repair recommended - can be handled by local workshop"
    elif severity_score <= 60:
        return "Professional repair required - authorized service center"
    elif severity_score <= 80:
        return "Major repair needed - specialized body shop required"
    else:
        return "Extensive damage - consider total loss assessment"

def display_assessment_results(results):
    """Display assessment results in a nice format"""
    
    st.subheader("Assessment Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    avg_severity = sum(r["severity_score"] for r in results) / len(results)
    total_cost = sum(r["estimated_cost"] for r in results)
    max_severity = max(r["severity_score"] for r in results)
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    
    col1.metric("Average Severity", f"{avg_severity:.1f}/100")
    col2.metric("Total Est. Cost", f"${total_cost:,.0f}")
    col3.metric("Max Severity", f"{max_severity}/100")
    col4.metric("Avg Confidence", f"{avg_confidence:.1f}%")
    
    st.divider()
    
    # Individual results
    for i, result in enumerate(results):
        with st.expander(f"{result['severity_color']} {result['filename']} - {result['severity_level']}", expanded=True):
            
            # Create columns for result display
            result_col1, result_col2 = st.columns([1, 1])
            
            with result_col1:
                st.write(f"**Damage Type:** {result['damage_type']}")
                st.write(f"**Severity Score:** {result['severity_score']}/100")
                st.write(f"**Severity Level:** {result['severity_level']}")
                st.write(f"**Confidence:** {result['confidence']}%")
                st.write(f"**Processing Time:** {result['processing_time']}s")
            
            with result_col2:
                st.write(f"**Estimated Cost:** ${result['estimated_cost']:,}")
                st.write(f"**Recommendation:**")
                st.info(result['recommended_action'])
            
            # Severity progress bar
            st.progress(result['severity_score'] / 100)
            
            # Action buttons
            btn_col1, btn_col2, btn_col3 = st.columns(3)
            btn_col1.button(f"Generate Report", key=f"report_{result['id']}")
            btn_col2.button(f"Email Results", key=f"email_{result['id']}")
            btn_col3.button(f"Save Assessment", key=f"save_{result['id']}")

def assessment_history_tab():
    """Display assessment history"""
    st.subheader("Assessment History")
    
    if "assessment_history" not in st.session_state or not st.session_state.assessment_history:
        st.info("No assessments yet. Upload images in the Image Upload tab to see history here.")
        return
    
    # Convert to DataFrame for better display
    df = pd.DataFrame(st.session_state.assessment_history)
    
    # Summary statistics
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assessments", len(df))
    col2.metric("Avg Severity", f"{df['severity_score'].mean():.1f}")
    col3.metric("Total Est. Cost", f"${df['estimated_cost'].sum():,}")
    col4.metric("Avg Confidence", f"{df['confidence'].mean():.1f}%")
    
    st.divider()
    
    # Filter options
    col1, col2 = st.columns(2)
    
    with col1:
        damage_filter = st.multiselect(
            "Filter by Damage Type",
            options=df['damage_type'].unique(),
            default=df['damage_type'].unique()
        )
    
    with col2:
        severity_filter = st.selectbox(
            "Filter by Severity Level",
            options=["All"] + list(df['severity_level'].unique())
        )
    
    # Apply filters
    filtered_df = df[df['damage_type'].isin(damage_filter)]
    if severity_filter != "All":
        filtered_df = filtered_df[filtered_df['severity_level'] == severity_filter]
    
    # Display filtered results
    st.dataframe(
        filtered_df[['filename', 'damage_type', 'severity_score', 'severity_level', 'estimated_cost', 'confidence', 'timestamp']],
        use_container_width=True
    )
    
    # Download button
    if st.button("Download History as CSV"):
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"damage_assessment_history_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

def settings_tab():
    """Settings for the computer vision module"""
    st.subheader("Computer Vision Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🎯 Assessment Parameters")
        
        sensitivity = st.slider("AI Sensitivity", 1, 10, 7, 
                               help="Higher values detect more minor damages")
        
        confidence_threshold = st.slider("Confidence Threshold", 50, 95, 75,
                                       help="Minimum confidence required for assessment")
        
        cost_multiplier = st.slider("Cost Estimation Factor", 0.5, 2.0, 1.0,
                                  help="Adjust cost estimation calculations")
    
    with col2:
        st.subheader("Display Options")
        
        show_confidence = st.checkbox("Show Confidence Scores", True)
        show_processing_time = st.checkbox("Show Processing Time", True)
        auto_save = st.checkbox("Auto-save Assessments", False)
        
        st.subheader("Advanced Settings")
        
        max_file_size = st.number_input("Max File Size (MB)", 1, 50, 10)
        supported_formats = st.multiselect(
            "Supported Formats",
            ["PNG", "JPG", "JPEG", "WEBP", "BMP"],
            default=["PNG", "JPG", "JPEG", "WEBP"]
        )
    
    if st.button("Save Settings"):
        st.success("Settings saved successfully!")
    
    if st.button("Reset to Defaults"):
        st.success("Settings reset to defaults!")

def get_image_details(image, uploaded_file):
    """Get technical details about uploaded image"""
    return {
        "filename": uploaded_file.name,
        "size": f"{uploaded_file.size / 1024:.1f} KB",
        "dimensions": f"{image.width} x {image.height}",
        "format": image.format,
        "mode": image.mode,
        "upload_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

# def show_example_interface():
#     """Show example interface when no files are uploaded"""
    
#     st.info("Upload vehicle damage images above to get started")
    
#     # Example results
#     st.subheader("Example Assessment")
    
#     example_data = {
#         "Feature": [
#             "Damage Detection",
#             "Severity Scoring",
#             "Cost Estimation",
#             "Confidence Rating",
#             "Repair Recommendations"
#         ],
#         "Description": [
#             "AI identifies type and location of vehicle damage",
#             "Scores damage severity from 1-100 scale",
#             "Estimates repair costs based on damage assessment",
#             "Provides confidence level of AI assessment",
#             "Suggests appropriate repair actions"
#         ]
#     }
    
#     st.table(pd.DataFrame(example_data))
    
    # Sample severity levels
    st.subheader("Severity Levels")
    
    severity_examples = [
        {"Level": "🟢 Minor (1-30)", "Description": "Small scratches, minor paint damage"},
        {"Level": "🟡 Moderate (31-60)", "Description": "Dents, significant scratches, panel damage"},
        {"Level": "🟠 Severe (61-80)", "Description": "Major collision damage, structural issues"},
        {"Level": "🔴 Critical (81-100)", "Description": "Extensive damage, potential total loss"}
    ]
    
    for item in severity_examples:
        st.write(f"**{item['Level']}:** {item['Description']}")