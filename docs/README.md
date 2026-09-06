# Folium Documentation

## Overview

Folium is a modern Electronic Health Records (EHR) system designed for healthcare providers. This documentation helps users understand how to use the platform effectively.

## Which Guide to Use

- **User guides** are the final, task-focused instructions for people using
  Folium. They describe supported workflows, not build or implementation detail.
  A supported user-guide claim is a product contract: it requires implementation
  and validation evidence. Planned behavior must be marked as planned and must
  not appear as a procedural user workflow until it is delivered.
- **Developer guides** preserve operational lessons, technical decisions, and
  tradeoffs for maintainers and coding agents. Start here before changing the
  related part of the system.
- **Administrator guides** cover deployment and configuration responsibilities.

## Quick Start

1. **Getting Started**: Set up your account and configure basic settings
2. **Patient Management**: Learn how to create and manage patient records
3. **Clinical Interactions**: Record patient visits and generate clinical notes
4. **Document Management**: Upload, view, and organize clinical documents
5. **AI Features**: Use voice notes and AI-powered summaries

## Documentation Structure

### User Guides

- [Managing Patients](user-guide/patients.md) - Create, edit, and search patient records
- [Encounters](user-guide/encounters.md) - Record patient contacts and work with
  their notes, summaries, and draft-support actions
- [Clinical Documents](user-guide/documents.md) - Upload and manage patient documents
- [Voice Notes](user-guide/voice-notes.md) - Record and transcribe clinical notes
- [AI Summaries](user-guide/summaries.md) - Generate and edit clinical summaries
- [Chart Review Drafts](user-guide/chart-review.md) - Request and review bounded AI draft support

### Developer Guides

- [Chart Review Agent Lessons](dev/chart-review-agent.md) - Local operations and bounded retrieval constraints
- [Local LLM Build Compatibility](dev/local-llm-builds.md) - A Linux ARM build
  lesson and the portable local-summarizer default
- [Clinical Data Model](dev/clinical-data-model.md) - Typed clinical-record
  relationships, migration conventions, and deferred scope
- [Clinical Data Migration](dev/clinical-data-migration.md) - Retired-record
  mapping and synthetic development-data reset procedure

### Administrator Guides

- [Installation](admin-guide/setup.md) - Deploy Folium for your organization
- [Configuration](admin-guide/configuration.md) - Environment variables and settings
- [Storage Setup](admin-guide/storage.md) - Configure MinIO, S3, or Azure Blob Storage
