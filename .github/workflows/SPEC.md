# CI/CD Workflows SPEC

## Structure

```
workflows/
├── deploy-backend.yml     # Orchestrator - manual trigger
├── deploy-frontend.yml    # Vercel auto-deploy on push
├── build.yml              # Cross-cloud Docker build + artifact upload
├── approval.yml           # Environment protection gate
├── azure-deploy.yml       # Azure Container Apps deployment
├── azure-terraform.yml    # Azure infrastructure
├── aws-deploy.yml         # AWS ECS/ECR deployment
└── aws-terraform.yml      # AWS infrastructure
```

Reusable workflow files must remain directly under `.github/workflows/`.
GitHub Actions does not support calling reusable workflows from subdirectories.

## Design Principles

- **Modular**: Cloud-specific logic uses provider-prefixed reusable workflows
- **Manual Deploy**: Backend deployments require explicit trigger with environment/cloud selection
- **Approval Gates**: All deployments go through environment-based approval (dev-approval, staging-approval, prod-approval)
- **Terraform Optional**: Infrastructure provisioning can be skipped if already exists
- **Multi-Cloud**: Same orchestrator supports Azure and AWS; add GCP by creating folder + conditional job

## Backend Pipeline Stages

1. **Build**: Docker image with multi-stage build, cached layers, artifact upload
2. **Approval**: Environment protection requires reviewer approval
3. **Infrastructure**: Terraform plan/apply (optional, cloud-specific)
4. **Deploy**: Push image to registry, update container service, health check

## Frontend Pipeline

Separate flow using Vercel:

1. Lint + type check
2. Build Next.js
3. Deploy to Vercel (preview on PR, production on main)

## Adding New Clouds

1. Create `workflows/{cloud}-deploy.yml` and `workflows/{cloud}-terraform.yml`
2. Add conditional job in orchestrator referencing new workflows
3. Add cloud option to workflow_dispatch inputs

## Adding New Services

1. Copy orchestrator pattern from deploy-backend.yml
2. Change image_name, context, and service-specific config
3. Reuse shared build/approval workflows
