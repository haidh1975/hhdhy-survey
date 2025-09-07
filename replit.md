# Survey Application for Social and Human Capital Impact on Business Sustainability

## Overview

This is a comprehensive web-based survey application built with Streamlit that focuses on collecting and analyzing data about the impact of social capital and human capital on sustainable business development in Hung Yen province, Vietnam. The application provides a complete survey lifecycle management system with multilingual support (Vietnamese-English) and advanced statistical analysis capabilities.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Framework**: Streamlit-based web application with multi-page navigation
- **UI Components**: Custom CSS styling with responsive design and gradient themes
- **Page Structure**: Modular page-based architecture with 5 main sections:
  - Survey Creation (pages/1_Create_Survey.py)
  - Survey Distribution (pages/2_Distribute_Survey.py) 
  - Response Viewing (pages/3_View_Responses.py)
  - Data Analysis (pages/4_Data_Analysis.py)
  - Survey Response Management (pages/5_Answer_Survey.py)
- **Session Management**: Streamlit session state for maintaining user data across page navigation
- **Authentication**: Role-based access control system with user authentication and session management

### Backend Architecture
- **Data Storage**: JSON-based file storage system for surveys, responses, and user data
- **Survey Engine**: Custom survey creation and management utilities
- **Analytics Engine**: Integrated statistical analysis with support for:
  - Cronbach's Alpha reliability testing
  - Exploratory Factor Analysis (EFA)
  - Multiple regression analysis
  - Confirmatory Factor Analysis (CFA)
- **Utility Modules**:
  - `utils/survey_utils.py`: Core survey operations
  - `utils/data_analysis.py`: Statistical calculations
  - `utils/visualization.py`: Chart generation with Plotly
  - `utils/advanced_analysis.py`: Advanced statistical methods
  - `utils/auth.py`: Authentication and authorization

### Data Management
- **Survey Storage**: JSON format with UUID-based survey identification
- **Response Collection**: Timestamp-based response tracking with flexible question type support
- **Question Types**: Multiple choice, Likert scales, text input, numeric input, checkbox selections
- **Export Capabilities**: Excel and CSV export functionality for data analysis

### Visualization and Analytics
- **Charting Library**: Plotly for interactive data visualizations
- **Statistical Analysis**: 
  - Factor analysis using factor-analyzer library
  - Regression modeling with scikit-learn and statsmodels
  - Descriptive statistics and correlation analysis
- **Report Generation**: Automated statistical reports with visual charts and summary tables

### Deployment Architecture
- **Web Server**: Nginx reverse proxy configuration
- **Process Management**: Supervisor for application lifecycle management
- **Environment**: Python virtual environment with pinned dependencies
- **Target Platform**: Ubuntu 20.04 LTS with automated deployment scripts

## External Dependencies

### Core Python Libraries
- **streamlit**: Web application framework (v1.32.2)
- **pandas**: Data manipulation and analysis (v2.1.4)
- **numpy**: Numerical computing (v1.26.4)
- **plotly**: Interactive visualization (v5.18.0)

### Statistical Analysis Libraries
- **factor-analyzer**: Factor analysis and reliability testing (v0.5.1)
- **scikit-learn**: Machine learning and statistical modeling (v1.4.0)
- **statsmodels**: Advanced statistical analysis (v0.14.1)

### Utility Libraries
- **openpyxl**: Excel file handling (v3.1.2)
- **qrcode**: QR code generation for survey distribution (v7.4.2)
- **pillow**: Image processing (v10.2.0)

### Infrastructure Dependencies
- **nginx**: Web server and reverse proxy
- **supervisor**: Process monitoring and management
- **python3-venv**: Virtual environment management

### Development Tools
- **React**: Frontend framework for enhanced survey interfaces (v18.2.0)
- **survey-core**: Survey.js library for advanced form capabilities (v1.9.97)
- **survey-react-ui**: React components for Survey.js (v1.9.97)

### Domain-Specific Configuration
- **Target Domain**: hhd.one with SSL configuration
- **Authentication System**: File-based user management with role-based permissions
- **Multilingual Support**: Vietnamese-English localization system