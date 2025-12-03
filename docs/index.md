---
layout: home
title: UNS Kobetsu Integrated
titleTemplate: ':title - UNS Kobetsu Documentation'
description: Comprehensive documentation for the UNS Kobetsu Keiyakusho management system

hero:
  name: UNS Kobetsu Integrated
  text: 個別契約書 Management System
  tagline: Comprehensive contract management system compliant with 労働者派遣法第26条
  image:
    src: /logo.svg
    alt: UNS Kobetsu Integrated
  actions:
    - theme: brand
      text: Get Started
      link: /getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/uns-kikaku/UNS-Kobetsu-Integrated

features:
  - icon: 📋
    title: Contract Management
    details: Complete lifecycle management for individual dispatch contracts with automated compliance checking.
  - icon: 👥
    title: Employee Management
    details: Comprehensive employee data management with visa tracking and assignment capabilities.
  - icon: 🏭
    title: Factory Integration
    details: Seamless integration with multiple factory locations and production facilities.
  - icon: 📄
    title: Document Generation
    details: Automated PDF generation for all required contract documents and forms.
  - icon: 🛡️
    title: Legal Compliance
    details: Built-in compliance with 労働者派遣法第26条 and all 16 required contract fields.
  - icon: 📊
    title: Analytics & Reporting
    details: Real-time dashboards and comprehensive reporting capabilities.
---

## 🚀 Quick Start

Get up and running with UNS Kobetsu Integrated in minutes:

```bash
# Clone the repository
git clone https://github.com/uns-kikaku/UNS-Kobetsu-Integrated.git
cd UNS-Kobetsu-Integrated

# Start with Docker Compose
docker compose up -d

# Access the application
# Frontend: http://localhost:3010
# Backend API: http://localhost:8000
```

## 📚 Documentation Sections

### [Getting Started](/getting-started)
Installation, configuration, and basic usage guides.

### [User Guides](/guides)
Step-by-step guides for managing contracts, employees, and documents.

### [API Documentation](/api)
Complete REST API reference with examples and authentication guides.

### [Development](/development)
Development setup, architecture overview, and contributing guidelines.

### [Deployment](/deployment)
Production deployment guides, monitoring, and maintenance procedures.

## 🔧 Key Features

### 📋 Contract Lifecycle Management
- **Contract Creation**: Automated contract generation with template-based forms
- **Compliance Checking**: Real-time validation against 労働者派遣法第26条 requirements
- **Renewal Management**: Automated renewal notifications and streamlined renewal process
- **Version Control**: Complete audit trail of all contract modifications

### 👥 Employee Data Management
- **Centralized Database**: Single source of truth for all employee information
- **Visa Tracking**: Automatic expiration alerts and compliance monitoring
- **Skill Management**: Categorized skill tracking and matching capabilities
- **Assignment History**: Complete record of all contract assignments

### 🏭 Multi-Factory Support
- **Location Management**: Support for multiple factory locations
- **Production Line Assignment**: Detailed assignment tracking and management
- **Contact Management**: Factory-specific contact information and communication
- **Capacity Planning**: Resource allocation and capacity management

### 📄 Automated Document Generation
- **PDF Generation**: Automatic creation of all required contract documents
- **Template System**: Customizable templates for different contract types
- **Batch Processing**: Bulk document generation and printing capabilities
- **Digital Signatures**: Support for digital signature workflows

## 🛡️ Compliance & Security

### 労働者派遣法第26条 Compliance
All contracts automatically include and validate the 16 required fields:
1. 派遣先の名称
2. 派遣先の住所
3. 派遣先の事業内容
4. 派遣先の指揮命令者
5. 個別契約書の作成日
6. 個別契約書の有効期間
7. 派遣労働者の氏名
8. 派遣労働者の生年月日
9. 派遣労働者の職種
10. 派遣労働者の業務内容
11. 派遣労働者の賃金
12. 派遣労働者の勤務時間
13. 派遣労働者の休憩時間
14. 派遣労働者の休日
15. 派遣労働者の安全衛生
16. 派遣労働者のその他

### Data Security
- **Role-Based Access**: Granular permission system for different user roles
- **Audit Logging**: Complete audit trail of all system activities
- **Data Encryption**: Encrypted storage for sensitive personal information
- **Backup Systems**: Automated backup and disaster recovery procedures

## 📊 System Architecture

### Backend (FastAPI)
- **RESTful API**: Comprehensive API with OpenAPI documentation
- **Database Layer**: PostgreSQL with optimized query performance
- **Authentication**: JWT-based authentication with role management
- **Background Jobs**: Celery for asynchronous task processing

### Frontend (Next.js)
- **Responsive Design**: Mobile-friendly interface with modern UI/UX
- **Real-time Updates**: WebSocket integration for live data updates
- **Component Architecture**: Reusable components for consistent UI
- **Performance Optimization**: Lazy loading and code splitting

### Infrastructure
- **Containerized**: Docker-based deployment for consistency
- **Scalable**: Horizontal scaling support with load balancing
- **Monitoring**: Comprehensive logging and performance metrics
- **CI/CD**: Automated testing and deployment pipelines

## 🚀 Getting Help

### Community Support
- **GitHub Discussions**: [Ask questions and share knowledge](https://github.com/uns-kikaku/UNS-Kobetsu-Integrated/discussions)
- **Issue Tracking**: [Report bugs and request features](https://github.com/uns-kikaku/UNS-Kobetsu-Integrated/issues)
- **Wiki**: [Community-maintained documentation](https://github.com/uns-kikaku/UNS-Kobetsu-Integrated/wiki)

### Professional Support
- **Documentation**: Comprehensive guides and API reference
- **Training Materials**: Video tutorials and step-by-step guides
- **Best Practices**: Industry-standard implementation guidelines

## 📈 Roadmap

### Version 1.1 (Q1 2024)
- [ ] Enhanced mobile application
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Integration with HR systems

### Version 1.2 (Q2 2024)
- [ ] AI-powered contract recommendations
- [ ] Advanced reporting features
- [ ] Workflow automation
- [ ] Enhanced security features

### Version 2.0 (Q3 2024)
- [ ] Microservices architecture
- [ ] Real-time collaboration features
- [ ] Advanced compliance automation
- [ ] Performance optimizations

---

<div style="text-align: center; margin-top: 2rem; padding: 1rem; background: var(--vp-c-bg-soft); border-radius: 8px;">
  <p>
    <strong>📖 Need more help?</strong><br>
    Check out our comprehensive documentation or join our community discussions.
  </p>
  <div style="margin-top: 1rem;">
    <a href="/getting-started" class="VPButton medium brand">Get Started</a>
    <a href="https://github.com/uns-kikaku/UNS-Kobetsu-Integrated/discussions" class="VPButton medium alt">Join Community</a>
  </div>
</div>