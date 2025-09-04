# Datasonic Insurance Management Platform

A comprehensive Streamlit application for managing insurance policies, claims, and automated damage assessment using computer vision and machine learning technologies.

## Features

### Core Functionality
- **Policy Management**: Create, update, and manage insurance policies with automated premium prediction
- **Claims Processing**: Handle insurance claims with document extraction and damage analysis
- **Document Intelligence**: Automated document processing and field extraction from emails and attachments
- **Computer Vision Integration**: AI-powered vehicle damage assessment with severity analysis
- **Premium Prediction**: ML-based premium calculation using advanced algorithms
- **Azure Blob Storage**: Secure document storage and management

### Advanced Capabilities
- **Automated Damage Detection**: Real-time analysis of vehicle damage with annotated images
- **Severity Assessment**: AI-driven risk evaluation (High/Medium/Low severity)
- **Multi-format Support**: Process emails, images, PDFs, and various document types
- **Real-time Dashboard**: Interactive dashboards for claims and damage analysis
- **Audit Logging**: Comprehensive activity tracking and performance monitoring

## Project Structure

```
streamlit-app/
├── .env                    # Environment variables and configuration
├── README.md               # Project documentation
├── media/                  # Application images and branding assets
├── src/                    # Source code for application functionality
│   ├── app.py              # Main application entry point
│   ├── auto_loader.py      # Automatic document processing and loading
│   ├── broker_insertion_date.py  # Broker data management
│   ├── claims_tabs.py      # Claims management interface
│   ├── edit_tabs.py        # Form editing interfaces
│   ├── insurer_broker_upload.py  # Insurer and broker data upload
│   ├── policy_tabs.py      # Policy management interface
│   ├── submission.py       # New submission processing
│   ├── theme.py            # UI theming and styling
│   ├── toba.py             # Terms of Business Agreement module
│   └── .streamlit/         # Streamlit configuration
├── utils/                  # Utility functions and helpers
│   ├── broker_form.py      # Broker form handling
│   ├── db_utils.py         # Database operations
│   ├── fabric_data_agent_client.py  # Microsoft Fabric integration
│   ├── fabric_data_agent_streamlit.py  # Fabric UI components
│   ├── insurer_form.py     # Insurer form handling
│   ├── lakehouse_schema.json  # Data schema definition
│   ├── metadata_manager.py  # Metadata management
│   ├── policy_forms.py     # Policy form handling
│   ├── policy_status_utils.py  # Policy status utilities
│   ├── schema_extractor.py  # Schema extraction utilities
│   ├── sql_alchemy_v2.py   # SQLAlchemy database interface
│   └── json/               # JSON templates for forms and data
```

## 🛠️ Setup Instructions

### Prerequisites
- Python 3.8 or higher
- SQL Server database access
- Azure Blob Storage account
- Computer Vision API endpoint
- Machine Learning API for premium prediction

### 1. Clone the Repository
```bash
git clone <repository-url>
cd Datasonic_App_Dev/streamlit-app
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Configuration
Create a `.env` file in the project root with the following variables:

```env
# Database Configuration
DB_SERVER=your_sql_server.database.windows.net
DB_DATABASE=your_database_name
DB_USERNAME=your_username
DB_PASSWORD=your_password

# Azure Blob Storage
AZURE_CONNECTION_STRING=your_azure_connection_string
AZURE_CONTAINER_NAME=your_container_name

# API Endpoints
API_URL=your_document_extraction_api_url
API_CODE=your_api_access_code
CV_ENDPOINT=your_computer_vision_api_url
ML_PREMIUM_API=your_ml_premium_prediction_api
ML_PREMIUM_BEARER=your_bearer_token

# Optional: Logging and Monitoring
LOG_LEVEL=INFO
```

### 4. Database Setup
Ensure your SQL Server database has the required tables:
- `New_Policies`
- `New_Claims` 
- `Documents`
- `App_Log`
- `Brokers`
- `Insurers`
- `APP_ML_DATA`
- `APP_CV_DATA`

### 5. Run the Application
```bash
streamlit run src/app.py
```

The application will be available at `http://localhost:8501`

## Usage Guide

### Policy Management
1. **New Policy Creation**: Navigate to "New Submission" tab
2. **Document Upload**: Drag and drop policy documents
3. **Automated Processing**: System extracts key fields automatically
4. **Premium Prediction**: ML model calculates optimal premium
5. **Review & Submit**: Validate data and create policy record

### Claims Processing
1. **Claim Registration**: Create new claim entries
2. **Document Upload**: Upload claim documents and damage photos
3. **Damage Analysis**: AI analyzes vehicle damage automatically
4. **Severity Assessment**: System provides risk evaluation
5. **Dashboard Review**: Monitor claim status and analytics

### Damage Assessment Workflow
1. **Image Upload**: Upload vehicle damage photos
2. **CV Analysis**: Computer vision detects and annotates damage
3. **Severity Scoring**: AI assigns High/Medium/Low severity
4. **Detailed Report**: View damage breakdown and repair recommendations
5. **Annotated Images**: Download marked-up images for reports

## 🔧 API Integrations

### Document Extraction API
- **Purpose**: Extract structured data from unstructured documents
- **Input**: Emails, PDFs, images
- **Output**: Classified data with extracted fields

### Computer Vision API
- **Purpose**: Vehicle damage detection and analysis
- **Input**: Vehicle damage images
- **Output**: Annotated images with damage severity assessment

### Premium Prediction API
- **Purpose**: ML-based premium calculation
- **Input**: Policy and risk factors
- **Output**: Predicted premium amount

## Dashboard Features

### Policy Dashboard
- Total policies overview
- Premium distribution analysis
- Policy type breakdowns
- Performance metrics

### Claims Dashboard
- Active claims monitoring
- Damage severity distribution
- Processing time analytics
- Cost projections

### Damage Analysis Dashboard
- Multi-image damage assessment
- Severity trend analysis
- Damage type categorization
- Annotated image gallery

## Security Features

- Environment variable configuration
- Secure database connections
- Azure Blob Storage encryption
- API authentication tokens
- Comprehensive audit logging

## 🚦 Deployment

### Local Development
```bash
streamlit run src/app.py
```

### Streamlit Cloud Deployment
1. Push code to GitHub repository
2. Connect repository to Streamlit Cloud
3. Configure secrets in Streamlit Cloud dashboard
4. Deploy automatically

### Production Considerations
- Use production database connections
- Configure proper SSL certificates
- Set up monitoring and alerting
- Implement backup strategies

## Logging and Monitoring

The application includes comprehensive logging for:
- User activities and interactions
- Document processing operations
- API calls and performance metrics
- Database operations and queries
- Error tracking and debugging


## Support

For technical support or questions:
- Check the logs in the application
- Review API endpoint documentation
- Contact the development team

## Version History

- **v1.0**: Initial release with basic policy/claims management
- **v2.0**: Added document intelligence and CV integration
- **v3.0**: Enhanced ML capabilities and dashboard analytics
- **Current**: Advanced damage assessment and premium prediction

---

**Note**: Ensure all environment variables are properly configured before running the application. The system requires active connections to SQL Server, Azure Blob Storage, and various API endpoints.