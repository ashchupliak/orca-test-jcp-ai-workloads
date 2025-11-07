# 🍎 Grazie AI Studio

A sophisticated, Apple-inspired web interface for the Grazie AI platform featuring multi-model comparison, advanced file processing, and premium aesthetics.

## ✨ Premium Features

### 🎨 **Apple-Inspired Design**
- **Glass Morphism Effects**: Beautiful translucent surfaces with backdrop blur
- **SF Pro Typography**: Apple's native font family for perfect readability
- **Smooth Animations**: Fluid transitions using cubic-bezier curves
- **Premium Color Palette**: Carefully crafted gradients and accent colors
- **Responsive Layout**: Seamless experience across all devices

### 🤖 **Multi-Model Comparison**
- **Parallel Processing**: Send queries to up to 4 models simultaneously
- **Real-time Streaming**: Watch all models respond in real-time
- **Model Selection Grid**: Visual cards showing capabilities and providers
- **Independent Chat Windows**: Each model gets its own dedicated chat area
- **Performance Comparison**: Compare response quality, speed, and style

### 📎 **Advanced File Processing**
- **Drag & Drop Interface**: Intuitive file upload with visual feedback
- **Multi-format Support**: Images, audio, documents, and archives
- **File Preview**: Smart file type detection and preview
- **Batch Upload**: Handle multiple files simultaneously

### 📦 **ZIP File Intelligence**
- **Automatic Extraction**: Unzip and analyze contents automatically
- **Content Analysis**: Read and understand text files within archives
- **File Mapping**: Complete inventory of archive contents
- **Text Integration**: Include file contents in AI conversations

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements_webapp.txt
```

### 2. Launch the Studio
```bash
python run_web_app.py
```

### 3. Access the Interface
**Open:** **http://localhost:8000**

## 🎯 Usage Guide

### **Step 1: Authentication**
1. Enter your JWT token in the secure password field
2. Select your environment (staging/production)
3. Click "Load Models" to fetch available models

### **Step 2: Model Selection**
1. Browse the model grid showing capabilities
2. Click up to 4 model cards to select them
3. Each selected model gets its own chat window

### **Step 3: File Upload (Optional)**
1. Drag files to the upload zone or click to browse
2. Supported formats:
   - **Images**: JPG, PNG, GIF, WebP
   - **Audio**: MP3, WAV, M4A, OGG
   - **Documents**: PDF, TXT, DOC, DOCX
   - **Archives**: ZIP files (auto-extracted)
3. Files are automatically analyzed and integrated

### **Step 4: Advanced Configuration**
- **System Message**: Set AI behavior and personality
- **Parameters**: Fine-tune temperature, top-p, tokens, seed
- **Streaming**: Enable real-time response generation

### **Step 5: Multi-Model Chat**
1. Type your message in the global input area
2. Press Enter or click send
3. Watch all selected models respond simultaneously
4. Compare responses, speed, and quality

## 🔧 Advanced Features

### **Parameter Tuning**
- **Temperature** (0.0-2.0): Control creativity and randomness
- **Top P** (0.0-1.0): Nucleus sampling for response diversity
- **Max Tokens**: Limit response length
- **Seed**: Deterministic outputs for consistent results

### **File Analysis Capabilities**
- **ZIP Processing**: Complete archive extraction and analysis
- **Image Analysis**: Visual content understanding
- **Audio Processing**: Audio content interpretation
- **Document Reading**: Text extraction and comprehension

### **Multi-Model Benefits**
- **Quality Comparison**: See which model performs best for your use case
- **Speed Benchmarking**: Compare response times
- **Style Variety**: Experience different AI personalities
- **Reliability**: Backup responses if one model fails

## 📋 Supported File Types

| Category | Formats | Features |
|----------|---------|----------|
| **Images** | JPG, PNG, GIF, WebP | Visual analysis, OCR, scene understanding |
| **Audio** | MP3, WAV, M4A, OGG | Transcription, content analysis |
| **Documents** | PDF, TXT, DOC, DOCX | Text extraction, content analysis |
| **Archives** | ZIP | Auto-extraction, content mapping, text reading |

## 🎨 Design Philosophy

### **Apple Aesthetics**
- **Minimalism**: Clean, uncluttered interfaces
- **Typography**: SF Pro font family for optimal readability
- **Spacing**: Generous whitespace and logical grouping
- **Colors**: Sophisticated gradients and accent colors

### **User Experience**
- **Intuitive Navigation**: Self-explaining interface elements
- **Visual Feedback**: Clear status indicators and animations
- **Responsive Design**: Adapts beautifully to any screen size
- **Accessibility**: High contrast ratios and semantic markup

## 🔒 Security & Privacy

- **Local Processing**: All file analysis happens locally
- **Secure Token Handling**: JWT tokens handled client-side only
- **No File Storage**: Uploaded files are processed and discarded
- **HTTPS Ready**: Production deployment with SSL/TLS

## 🛠️ Technical Architecture

### **Frontend**
- **Pure HTML/CSS/JS**: No framework dependencies
- **Modern CSS**: CSS Grid, Flexbox, custom properties
- **ES6+ JavaScript**: Async/await, fetch API, modules
- **Progressive Enhancement**: Works without JavaScript for basic features

### **Backend**
- **Flask Framework**: Lightweight and efficient
- **Streaming Support**: Real-time response delivery
- **File Processing**: ZIP extraction, content analysis
- **Error Handling**: Comprehensive error management

## 📊 Performance

- **Multi-threading**: Parallel model processing
- **Streaming Responses**: Real-time output delivery
- **Efficient File Handling**: Memory-conscious processing
- **Responsive UI**: 60fps animations and interactions

## 🆕 What's New

### **v2.0 - AI Studio**
- ✅ Complete UI redesign with Apple aesthetics
- ✅ Multi-model comparison (up to 4 models)
- ✅ Advanced file upload and processing
- ✅ ZIP file extraction and analysis
- ✅ Glass morphism visual effects
- ✅ Improved mobile responsiveness

## 🎉 Getting the Most Out of AI Studio

### **Multi-Model Strategies**
1. **Quality Testing**: Compare creative vs. analytical models
2. **Speed Optimization**: Find fastest models for your use case
3. **Specialized Tasks**: Use different models for different aspects
4. **Backup Responses**: Ensure reliability with multiple models

### **File Processing Tips**
1. **ZIP Archives**: Great for analyzing entire projects or codebases
2. **Image Analysis**: Upload screenshots for UI/UX feedback
3. **Document Review**: Get insights on PDFs and documents
4. **Code Analysis**: ZIP your project for comprehensive code review

## 🎯 Use Cases

- **Development**: Code review, bug analysis, architecture discussions
- **Design**: UI/UX feedback, visual analysis, design critique
- **Research**: Document analysis, data interpretation
- **Content**: Writing assistance, editing, style comparison
- **Education**: Learning material analysis, concept explanation

---

**Ready to experience the future of AI interaction?** 
**🚀 Launch Grazie AI Studio: http://localhost:8000** 