## 📑 Table of Contents


1. [Agent Blueprint](#agent-blueprint)
   - [🚀 Key Features](#-key-features)
   - [⚠️ Critical Requirement: Agent Name Convention](#️-critical-requirement-agent-name-convention)
     - [Why This is Required](#why-this-is-required)
     - [Examples](#examples)

2. [Development Guidelines](#development-guidelines)
   - [Pre-required](#pre-required)
     - [System Requirements](#system-requirements)
     - [Required API Keys & Tokens](#required-api-keys--tokens)
     - [AWS Requirements (Handled Automatically)](#aws-requirements-handled-automatically)
   - [Technology Stack](#technology-stack)
     - [Core Framework](#core-framework)
     - [AI & Integration](#ai--integration)
     - [Cloud Infrastructure](#cloud-infrastructure)
     - [DevOps & CI/CD](#devops--cicd)
     - [Development Tools](#development-tools)
   - [To Run the Agent](#to-run-the-agent)

3. [Script to Deploy the Blueprint (not on Replit)](#script-to-deploy-the-blueprint-not-on-replit)


# Agent Blueprint

This repository provides a foundational structure for creating AI agents with optimized AWS Lambda deployment. It offers a complete starting point for building custom AI functionalities with built-in CI/CD, infrastructure management, and secure secrets handling.

## 🚀 Key Features

- **Multi-Agent Types**: Support for general, gimlet, mojito, Old Fashioned, and daiquiri agent configurations
- **AWS Integration**: Seamless Lambda deployment with S3 storage and API Gateway
- **Secure Secrets**: Automatic GitHub secrets → AWS SSM Parameter Store synchronization
- **Environment Management**: Separate dev/prod environments with branch-based deployment
- **Latest-Only Storage**: Optimized S3 deployment strategy with automatic cleanup

## ⚠️ **Critical Requirement: Agent Name Convention**

**Your agent name MUST start with `agent-`** (e.g., `agent-my-assistant`, `agent-data-processor`)

### Why This is Required:
- **AWS OIDC Authentication**: GitHub Actions uses OpenID Connect to securely authenticate with AWS
- **Role Permissions**: The AWS IAM role is configured to trust repositories starting with `agent-`
- **Deployment Security**: This prefix ensures only authorized agent repositories can deploy to AWS
- **Automatic Failure**: Without this prefix, GitHub Actions deployment will fail with authentication errors

### Examples:
- ✅ `agent-customer-support`
- ✅ `agent-data-analyzer`  
- ✅ `agent-content-moderator`
- ✅ `agent-slack-bot`
- ❌ `my-agent` (missing prefix)
- ❌ `bot-helper` (wrong prefix)
- ❌ `customer-agent` (prefix in wrong position)

Fork this repository and customize the `AGENT_NAME` variable to kickstart your own agent development.

---

## Development Guidelines

### Pre-required

#### System Requirements
- **Python**: >= 3.11.3
- **FastAPI**: >= 0.70.0
- **Uvicorn**: >= 0.15.0

#### Required API Keys & Tokens
- **GitHub Personal Access Token**: 
  - Create at: https://github.com/settings/tokens
  - Required scopes: `repo`, `workflow`, `write:packages`
  - Used for: Repository creation, secrets management, CI/CD
- **OpenAI API Key**:
  - Get from: https://platform.openai.com/api-keys
  - Used for: AI model access and agent functionality

#### AWS Requirements (Handled Automatically)
- AWS Lambda execution role (created by Terraform)
- S3 bucket for deployment artifacts (managed by GitHub Actions)
- SSM Parameter Store for secrets (auto-configured)
- API Gateway for HTTP endpoints (deployed via Terraform)

### Technology Stack

#### Core Framework
- **FastAPI**: High-performance web framework for building APIs
- **Uvicorn**: ASGI server for running FastAPI applications
- **Poetry**: Dependency management and packaging
- **Pydantic**: Data validation and settings management

#### AI & Integration
- **OpenAI GPT**: Large language models for AI capabilities
- **Python-dotenv**: Environment variable management
- **Requests**: HTTP client for external API calls

#### Cloud Infrastructure
- **AWS Lambda**: Serverless compute for agent execution
- **Amazon S3**: Deployment package storage with latest-only strategy
- **API Gateway**: HTTP API endpoints and routing
- **SSM Parameter Store**: Secure secrets and configuration management
- **CloudWatch**: Logging and monitoring

#### DevOps & CI/CD
- **GitHub Actions**: Automated testing, building, and deployment
- **Terraform**: Infrastructure as Code for AWS resources
- **Docker**: Containerization for consistent environments
- **GitHub Secrets**: Secure storage of sensitive configuration

#### Development Tools
- **Git**: Version control and collaboration
- **GitHub**: Repository hosting and project management
- **VS Code / PyCharm**: Recommended IDEs with Python support
- **Postman / Thunder Client**: API testing and documentation

### To Run the Agent

Before running the below script set the aws and OpenAI credentials or any credentials used in the code, as the agent don't read from the .env file
```
export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_ACCESS_KEY
export AWS_DEFAULT_REGION=eu-west-2
export OPENAI_API_KEY=YOUR_API_KEY
```
Run:
```
uvicorn smart_agent.main:app --reload
```


## Script to deploy the blueprint not on Replit
Note: Set `deploy_target` in the script to choose the deployment platform:
- `lambda`: Traditional Lambda with ZIP deployment (best for simple agents)
- `lambda_ecr`: Lambda with ECR container (supports larger dependencies, Chrome, etc.)
- `ecs`: ECS Fargate with shared ALB (for long-running operations)

For ECS, the workflow ensures a DynamoDB table `ecs-agents-jobs-state` exists and uses it for job state.

**ECS Shared Resources Policy**: For ECS deployment, agents use shared infrastructure to optimize resource usage and reduce costs:

**Shared Clusters**: Agents use `agents-dev` and `agents-prod` clusters instead of individual clusters per agent.
- Uses existing shared cluster if available
- Creates shared cluster only if it doesn't exist
- Imports existing clusters into Terraform state management

**Shared Load Balancer**: All agents share the same ALB (`activate-bar-alb`) with environment-aware path-based routing:
- **Dev**: `http(s)://activate-bar-alb-90191003.eu-west-2.elb.amazonaws.com/{agent_name}-dev/*`
- **Prod**: `http(s)://activate-bar-alb-90191003.eu-west-2.elb.amazonaws.com/{agent_name}-prod/*`
- Each agent+environment gets its own target group and listener rules
- Both dev and prod versions can run simultaneously
- Automatic priority assignment prevents conflicts

Tip: The script sets `commit.gpgsign=false` and disables git hooks locally to prevent interactive prompts that can cause hangs in headless terminals. Remove those lines in `initialize_new_git_repo` if you need signing or hooks.
```
#!/bin/bash

# ====== CONFIGURATION SECTION ======
# CUSTOMIZE THESE VALUES:

# Enter your new agent name (this will be used as repository name)
AGENT_NAME="agent-aws-testing"

# GitHub token will be read from environment variable GH_TOKEN
# Set this in your environment: export GH_TOKEN="your_token_here"
GH_TOKEN="${GH_TOKEN}"

# Uncomment only one agent_type at a time
agent_type='general'
# agent_type='gimlet'
# agent_type='mojito'
# agent_type='daiquiri'
# agent_type='oldFashioned'

# Choose deployment target: 'lambda', 'lambda_ecr', or 'ecs'
deploy_target='lambda'
# deploy_target='lambda_ecr'  # Lambda with ECR container (supports larger dependencies)
# deploy_target='ecs'         # ECS Fargate with shared ALB

# ====== END CONFIGURATION SECTION ======

# Convert agent name to repository-friendly format (lowercase, replace spaces with hyphens)
REPO_NAME=$(echo "$AGENT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/ /-/g' | sed 's/[^a-z0-9-]//g')
BLUEPRINT_REPO_URL="https://$GH_TOKEN:x-oauth-basic@github.com/Activate-Intelligence/agent-blueprint.git"
PROJECT_NAME="smart_agent"  # Keep this fixed as smart_agent
GITHUB_ORG="Activate-Intelligence"
TEMP_CLONE_DIR="blueprint_temp"

# Function to prompt for missing environment variables
prompt_missing_variables() {
    local missing_vars=("$@")
    
    echo "**"
    echo -e "\e[33mMissing required environment variables detected.\e[0m"
    echo -e "\e[33mPlease provide the following values:\e[0m"
    echo "**"
    
    for var in "${missing_vars[@]}"; do
        case $var in
            "GH_TOKEN")
                echo -e "\e[32mEnter your GitHub Personal Access Token:\e[0m"
                echo -e "\e[33m(Create one at: https://github.com/settings/tokens)\e[0m"
                echo -e "\e[33m(Required scopes: repo, workflow, write:packages)\e[0m"
                read -s -p "GH_TOKEN: " input_value
                echo ""
                if [ -n "$input_value" ]; then
                    export GH_TOKEN="$input_value"
                    GH_TOKEN="$input_value"
                    echo -e "\e[32m✓ GitHub token set\e[0m"
                else
                    echo -e "\e[31m❌ GitHub token cannot be empty\e[0m"
                    return 1
                fi
                ;;
            "OPENAI_API_KEY")
                echo -e "\e[32mEnter your OpenAI API Key:\e[0m"
                echo -e "\e[33m(Get one at: https://platform.openai.com/api-keys)\e[0m"
                read -s -p "OPENAI_API_KEY: " input_value
                echo ""
                if [ -n "$input_value" ]; then
                    export OPENAI_API_KEY="$input_value"
                    echo -e "\e[32m✓ OpenAI API key set\e[0m"
                else
                    echo -e "\e[31m❌ OpenAI API key cannot be empty\e[0m"
                    return 1
                fi
                ;;
        esac
        echo ""
    done
    
    echo -e "\e[32m✓ All required environment variables have been set\e[0m"
    echo "**"
    return 0
}

# Function to set repository secrets using GitHub API
set_repo_secrets_api() {
    echo "Setting repository secrets using GitHub API..."

    # Get repository public key for encryption
    public_key_response=$(curl -s -H "Authorization: token $GH_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/secrets/public-key")

    if [ $? -ne 0 ]; then
        echo -e "\e[31m❌ Failed to get repository public key\e[0m"
        return 1
    fi

    # Extract public key and key_id using Python for more reliable JSON parsing
    key_data=$(python3 -c "
import json
import sys
try:
    data = json.loads('''$public_key_response''')
    print(f\"{data['key']}|||{data['key_id']}\")
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")

    if [[ "$key_data" == ERROR* ]]; then
        echo -e "\e[31m❌ Failed to parse public key response: $key_data\e[0m"
        echo "Response: $public_key_response"
        return 1
    fi

    PUBLIC_KEY=$(echo "$key_data" | cut -d'|' -f1)
    KEY_ID=$(echo "$key_data" | cut -d'|' -f4)

    if [ -z "$PUBLIC_KEY" ] || [ -z "$KEY_ID" ]; then
        echo -e "\e[31m❌ Failed to extract public key information\e[0m"
        echo "Key data: $key_data"
        return 1
    fi

    echo -e "\e[32m✓ Successfully retrieved repository public key\e[0m"

    # Function to encrypt and set a secret
    set_secret() {
        local secret_name=$1
        local secret_value=$2

        echo "Setting secret: $secret_name"

        # Use Python to encrypt the secret (sodium encryption)
        encrypted_value=$(python3 -c "
import base64
import sys
try:
    from nacl import encoding, public
    public_key = public.PublicKey('$PUBLIC_KEY', encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt('$secret_value'.encode('utf-8'))
    print(base64.b64encode(encrypted).decode('utf-8'))
except ImportError:
    print('ERROR: PyNaCl not installed')
    sys.exit(1)
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")

        if [[ "$encrypted_value" == ERROR* ]]; then
            echo -e "\e[33m⚠ Encryption failed for $secret_name: $encrypted_value\e[0m"
            echo -e "\e[33m  Installing PyNaCl and retrying...\e[0m"

            # Install PyNaCl
            pip install --no-user pynacl >/dev/null 2>&1

            # Retry encryption
            encrypted_value=$(python3 -c "
import base64
import sys
try:
    from nacl import encoding, public
    public_key = public.PublicKey('$PUBLIC_KEY', encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt('$secret_value'.encode('utf-8'))
    print(base64.b64encode(encrypted).decode('utf-8'))
except Exception as e:
    print(f'ERROR: {e}')
    sys.exit(1)
")

            if [[ "$encrypted_value" == ERROR* ]]; then
                echo -e "\e[31m❌ Failed to encrypt $secret_name after installing PyNaCl\e[0m"
                return 1
            fi
        fi

        # Set the secret using GitHub API
        response=$(curl -s -w "%{http_code}" -X PUT \
            -H "Authorization: token $GH_TOKEN" \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Content-Type: application/json" \
            -d "{
                \"encrypted_value\": \"$encrypted_value\",
                \"key_id\": \"$KEY_ID\"
            }" \
            "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/secrets/$secret_name")

        http_code="${response: -3}"
        response_body="${response%???}"

        if [ "$http_code" = "201" ] || [ "$http_code" = "204" ]; then
            echo -e "\e[32m✓ Set secret: $secret_name\e[0m"
        else
            echo -e "\e[31m❌ Failed to set secret $secret_name (HTTP: $http_code)\e[0m"
            echo "Response: $response_body"
            return 1
        fi
    }

    # Set all required secrets
    echo "Setting repository secrets..."

    set_secret "APP_PORT" "${APP_PORT:-8000}"
    set_secret "APP_HOST" "${APP_HOST:-0.0.0.0}"
    set_secret "GH_TOKEN" "$GH_TOKEN"
    set_secret "ALLOW_ORIGINS" "${ALLOW_ORIGINS:-http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar}"
    set_secret "OPENAI_API_KEY" "${OPENAI_API_KEY:-Enter_Key}"
    set_secret "AGENT_NAME" "$AGENT_NAME"
    set_secret "AGENT_TYPE" "$agent_type"
    set_secret "AGENT_EXECUTE_LIMIT" "${AGENT_EXECUTE_LIMIT:-1}"

    echo -e "\e[32m✓ Repository secrets configured successfully\e[0m"
    return 0
}

# Function to set repository secrets using gh CLI (fallback)
set_repo_secrets_gh() {
    echo "Setting repository secrets using gh CLI..."

    if ! command -v gh >/dev/null 2>&1; then
        echo -e "\e[33m⚠ gh CLI not found, skipping gh CLI method\e[0m"
        return 1
    fi

    # Check if gh is authenticated
    if ! gh auth status >/dev/null 2>&1; then
        echo -e "\e[33m⚠ gh CLI not authenticated, attempting login with token\e[0m"
        echo "$GH_TOKEN" | gh auth login --with-token

        if ! gh auth status >/dev/null 2>&1; then
            echo -e "\e[31m❌ Failed to authenticate gh CLI\e[0m"
            return 1
        fi
    fi

    # Set secrets using gh CLI
    echo "$APP_PORT" | gh secret set APP_PORT -R "$GITHUB_ORG/$REPO_NAME"
    echo "$APP_HOST" | gh secret set APP_HOST -R "$GITHUB_ORG/$REPO_NAME"
    echo "$GH_TOKEN" | gh secret set GH_TOKEN -R "$GITHUB_ORG/$REPO_NAME"
    echo "$ALLOW_ORIGINS" | gh secret set ALLOW_ORIGINS -R "$GITHUB_ORG/$REPO_NAME"
    echo "$OPENAI_API_KEY" | gh secret set OPENAI_API_KEY -R "$GITHUB_ORG/$REPO_NAME"
    echo "$AGENT_NAME" | gh secret set AGENT_NAME -R "$GITHUB_ORG/$REPO_NAME"
    echo "$agent_type" | gh secret set AGENT_TYPE -R "$GITHUB_ORG/$REPO_NAME"
    echo "$AGENT_EXECUTE_LIMIT" | gh secret set AGENT_EXECUTE_LIMIT -R "$GITHUB_ORG/$REPO_NAME"

    echo -e "\e[32m✓ Repository secrets set via gh CLI\e[0m"
    return 0
}

# Function to create GitHub repository with README and set team permissions
create_github_repo_with_readme() {
    echo "Creating new private GitHub repository: $REPO_NAME in $GITHUB_ORG organization..."

    # Create repository using GitHub API (empty repository)
    response=$(curl -s -w "%{http_code}" -X POST \
        -H "Authorization: token $GH_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -d "{
            \"name\": \"$REPO_NAME\",
            \"description\": \"$AGENT_NAME - AI Agent built with oneForAll blueprint\",
            \"private\": true,
            \"auto_init\": false
        }" \
        "https://api.github.com/orgs/$GITHUB_ORG/repos")

    # Extract HTTP status code (last 3 characters)
    http_code="${response: -3}"
    response_body="${response%???}"

    if [ "$http_code" = "201" ]; then
        echo -e "\e[32m✓ Private repository '$REPO_NAME' created successfully\e[0m"
        
        # Add team permissions after successful repository creation
        add_team_permissions
        
    elif [ "$http_code" = "422" ]; then
        if echo "$response_body" | grep -q "already exists"; then
            echo -e "\e[33m⚠ Repository '$REPO_NAME' already exists\e[0m"
            
            # Still try to add team permissions for existing repository
            add_team_permissions
        else
            echo -e "\e[31m❌ Failed to create repository: $response_body\e[0m"
            exit 1
        fi
    else
        echo -e "\e[31m❌ Failed to create repository. HTTP Code: $http_code\e[0m"
        echo -e "\e[31mResponse: $response_body\e[0m"
        exit 1
    fi

    echo -e "\e[32m✓ Private repository created/verified\e[0m"
    echo -e "\e[32m📂 Repository URL: https://github.com/$GITHUB_ORG/$REPO_NAME\e[0m"
}

# Function to add team permissions to repository
add_team_permissions() {
    echo "Adding @Activate-Intelligence/ai-dev team with admin access..."
    
    # Add ai-dev team with admin permissions
    team_response=$(curl -s -w "%{http_code}" -X PUT \
        -H "Authorization: token $GH_TOKEN" \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Content-Type: application/json" \
        -d "{
            \"permission\": \"admin\"
        }" \
        "https://api.github.com/orgs/$GITHUB_ORG/teams/ai-dev/repos/$GITHUB_ORG/$REPO_NAME")

    # Extract HTTP status code
    team_http_code="${team_response: -3}"
    team_response_body="${team_response%???}"

    if [ "$team_http_code" = "204" ]; then
        echo -e "\e[32m✓ Successfully added @Activate-Intelligence/ai-dev team with admin access\e[0m"
    elif [ "$team_http_code" = "404" ]; then
        echo -e "\e[33m⚠ Team 'ai-dev' not found in organization. Skipping team permissions.\e[0m"
        echo -e "\e[33m  You may need to add team permissions manually at:\e[0m"
        echo -e "\e[33m  https://github.com/$GITHUB_ORG/$REPO_NAME/settings/access\e[0m"
    else
        echo -e "\e[33m⚠ Failed to add team permissions (HTTP: $team_http_code)\e[0m"
        echo -e "\e[33m  Response: $team_response_body\e[0m"
        echo -e "\e[33m  You can add team permissions manually at:\e[0m"
        echo -e "\e[33m  https://github.com/$GITHUB_ORG/$REPO_NAME/settings/access\e[0m"
    fi
}

# Function to create GitHub workflow file with S3 deployment and cleanup
create_github_workflow() {
    cat > ".github/workflows/deploy.yml" <<'EOF'
name: Deploy __REPO_NAME__ Lambda

on:
  push:
    branches: [main, 'prod**']
  pull_request:
    branches: ['prod**']

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      TF_VAR_function_name: __REPO_NAME__
      TF_VAR_aws_region: eu-west-2
      TF_VAR_jobs_table_name: agents-jobs-state
      S3_BUCKET: 533267084389-lambda-artifacts
      
    steps:
      - uses: actions/checkout@v4
      
      - name: Determine Environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (main branch)"
          elif [[ "${{ github.ref }}" == refs/heads/prod* ]]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
            echo "Environment: prod (production branch)"
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (default)"
          fi
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          
      - name: Install dependencies
        run: |
          pip install -r smart_agent/requirements.txt
          pip install mangum boto3
          
      - name: Package Lambda
        run: |
          python scripts/package-lambda.py
          
      - name: AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v3
        with:
          role-to-assume: arn:aws:iam::533267084389:role/github
          aws-region: eu-west-2
          
      - name: Create S3 bucket if not exists
        run: |
          echo "Checking if S3 bucket exists..."
          if aws s3api head-bucket --bucket "$S3_BUCKET" 2>/dev/null; then
            echo "✓ S3 bucket $S3_BUCKET already exists"
          else
            echo "Creating S3 bucket $S3_BUCKET..."
            aws s3api create-bucket \\
              --bucket "$S3_BUCKET" \\
              --region eu-west-2 \\
              --create-bucket-configuration LocationConstraint=eu-west-2
            
            # Enable versioning
            aws s3api put-bucket-versioning \\
              --bucket "$S3_BUCKET" \\
              --versioning-configuration Status=Enabled
            
            # Enable encryption
            aws s3api put-bucket-encryption \\
              --bucket "$S3_BUCKET" \\
              --server-side-encryption-configuration '{
                "Rules": [
                  {
                    "ApplyServerSideEncryptionByDefault": {
                      "SSEAlgorithm": "AES256"
                    }
                  }
                ]
              }'
            
            # Configure lifecycle policy to keep only latest version
            aws s3api put-bucket-lifecycle-configuration \\
              --bucket "$S3_BUCKET" \\
              --lifecycle-configuration '{
                "Rules": [
                  {
                    "ID": "KeepLatestVersionOnly",
                    "Status": "Enabled",
                    "Filter": {},
                    "NoncurrentVersionExpiration": {
                      "NoncurrentDays": 1
                    },
                    "ExpiredObjectDeleteMarker": true
                  }
                ]
              }'
            
            echo "✓ S3 bucket $S3_BUCKET created successfully"
          fi
          
      - name: Clean up old packages and upload latest
        id: upload
        run: |
          ENVIRONMENT=${{ steps.env.outputs.environment }}
          S3_PREFIX="__REPO_NAME__/$ENVIRONMENT/"
          S3_KEY="${S3_PREFIX}deployment-latest.zip"
          
          echo "Cleaning up old packages for __REPO_NAME__ in environment $ENVIRONMENT..."
          echo "Target S3 prefix: s3://$S3_BUCKET/${S3_PREFIX}"
          
          # List existing files for this specific agent and environment only
          aws s3 ls "s3://$S3_BUCKET/${S3_PREFIX}" || echo "No existing files found for __REPO_NAME__/$ENVIRONMENT"
          
          # Delete files only in the current agent's environment folder
          aws s3 rm "s3://$S3_BUCKET/${S3_PREFIX}" --recursive || echo "No files to delete for __REPO_NAME__/$ENVIRONMENT"
          
          echo "Uploading latest Lambda package to S3..."
          aws s3 cp deployment.zip "s3://$S3_BUCKET/${S3_KEY}" --metadata "deployment-timestamp=$(date -u +%Y%m%d%H%M%S),git-sha=${{ github.sha }},environment=$ENVIRONMENT"
          
          echo "s3_key=${S3_KEY}" >> $GITHUB_OUTPUT
          echo "s3_bucket=$S3_BUCKET" >> $GITHUB_OUTPUT
          echo "✓ Latest package uploaded to s3://$S3_BUCKET/${S3_KEY}"
          
          # Verify upload
          aws s3 ls "s3://$S3_BUCKET/${S3_KEY}"
          
      - name: Upload all secrets to SSM
        env:
          SECRETS_JSON: ${{ toJson(secrets) }}
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          echo "Uploading all repository secrets to SSM Parameter Store..."
          
          # Function to create or update SSM parameter
          create_or_update_parameter() {
            local param_name="$1"
            local param_value="$2"
            local param_type="$3"
            
            echo "Processing parameter: $param_name"
            
            # First, try to create the parameter with tags (new parameter)
            if aws ssm put-parameter \
              --name "$param_name" \
              --value "$param_value" \
              --type "$param_type" \
              --tags Key=Name,Value="__REPO_NAME__-$(basename $param_name)" Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=GitHubActions \
              --no-overwrite \
              2>/dev/null; then
              echo "✓ Created new parameter: $param_name"
            else
              # Parameter exists, update it (without tags)
              if aws ssm put-parameter \
                --name "$param_name" \
                --value "$param_value" \
                --type "$param_type" \
                --overwrite; then
                echo "✓ Updated existing parameter: $param_name"
                
                # Try to add/update tags separately (ignore errors if tags already exist)
                aws ssm add-tags-to-resource \
                  --resource-type "Parameter" \
                  --resource-id "$param_name" \
                  --tags Key=Name,Value="__REPO_NAME__-$(basename $param_name)" Key=Environment,Value=$ENVIRONMENT Key=ManagedBy,Value=GitHubActions \
                  2>/dev/null || echo "Note: Could not update tags for $param_name (may already exist)"
              else
                echo "❌ Failed to create/update parameter: $param_name"
                return 1
              fi
            fi
          }
          
          # Parse secrets and upload each one
          echo "$SECRETS_JSON" | jq -r 'to_entries[] | select(.key != "GITHUB_TOKEN") | @base64' | while read -r entry; do
            # Decode the entry
            decoded=$(echo $entry | base64 --decode)
            
            # Extract key and value
            key=$(echo $decoded | jq -r '.key')
            value=$(echo $decoded | jq -r '.value')
            
            # Skip empty values
            if [ -n "$value" ] && [ "$value" != "null" ]; then
              # Determine parameter type based on key name
              if [[ $key == *"API_KEY"* ]] || [[ $key == *"TOKEN"* ]] || [[ $key == *"SECRET"* ]] || [[ $key == *"PASSWORD"* ]]; then
                param_type="SecureString"
              else
                param_type="String"
              fi
              
              # Create full parameter name with environment
              param_name="/app/__REPO_NAME__/$ENVIRONMENT/$key"
              
              # Create or update the parameter
              create_or_update_parameter "$param_name" "$value" "$param_type"
            else
              echo "⚠ Skipping empty secret: $key"
            fi
          done
          
          echo "✓ All secrets processed for SSM Parameter Store"
          
      - name: Verify SSM parameters
        run: |
          ENVIRONMENT=${{ steps.env.outputs.environment }}
          echo "Verifying uploaded parameters..."
          aws ssm describe-parameters \
            --parameter-filters Key=Name,Values="/app/__REPO_NAME__/$ENVIRONMENT/" \
            --query 'Parameters[].{Name:Name,Type:Type,LastModifiedDate:LastModifiedDate}' \
            --output table
            
      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_wrapper: false
          
      - name: Terraform init + apply
        env:
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          # Update terraform backend key with environment
          terraform -chdir=terraform init \
            -backend-config="region=eu-west-2" \
            -backend-config="bucket=533267084389-tf-state" \
            -backend-config="key=aws/$ENVIRONMENT/agents/__REPO_NAME__" \
            -backend-config="encrypt=true" \
            -backend-config="use_lockfile=true"
            
          terraform -chdir=terraform apply -auto-approve \
            -var="s3_bucket=${{ steps.upload.outputs.s3_bucket }}" \
            -var="s3_key=${{ steps.upload.outputs.s3_key }}" \
            -var="environment=$ENVIRONMENT"
            
      - name: Show endpoints
        run: |
          cd terraform
          echo "::notice title=Environment::\${{ steps.env.outputs.environment }}"
          echo "::notice title=Lambda Function URL::\$(terraform output -raw function_url)"
          echo "::notice title=Function Name::\$(terraform output -raw function_name)"
          echo "::notice title=DynamoDB Table::\$(terraform output -raw dynamodb_table_name)"
          echo "::notice title=S3 Package Location::s3://\${{ steps.upload.outputs.s3_bucket }}/\${{ steps.upload.outputs.s3_key }}"
          echo "::notice title=SSM Parameters::\$(aws ssm describe-parameters --parameter-filters Key=Name,Values=/app/__REPO_NAME__/\${{ steps.env.outputs.environment }}/ --query 'Parameters[].Name' --output table)"
          
      - name: Clean up local artifacts
        run: |
          echo "Cleaning up local build artifacts..."
          rm -f deployment.zip
          rm -rf package/
          echo "✓ Local artifacts cleaned up"
EOF

    echo "✓ Created workflow file at .github/workflows/deploy.yml"
    # Replace placeholders with actual repo name
    if sed --version >/dev/null 2>&1; then
        sed -i -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
    else
        sed -i '' -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
    fi
}

# Function to create GitHub workflow file for ECS Fargate deployment
create_github_workflow_ecs() {
    cat > ".github/workflows/deploy.yml" <<'EOF'
name: Deploy __REPO_NAME__ ECS

on:
  push:
    branches: [main, 'prod**']
  pull_request:
    branches: ['prod**']

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      TF_VAR_function_name: __REPO_NAME__
      TF_VAR_aws_region: eu-west-2
      TF_VAR_deployment_type: ecs
      TF_VAR_jobs_table_name: ecs-agents-jobs-state
      AWS_REGION: eu-west-2
    steps:
      - uses: actions/checkout@v4

      - name: Determine Environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (main branch)"
          elif [[ "${{ github.ref }}" == refs/heads/prod* ]]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
            echo "Environment: prod (production branch)"
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (default)"
          fi

      - name: AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v3
        with:
          role-to-assume: arn:aws:iam::533267084389:role/github
          aws-region: eu-west-2

      - name: Ensure DynamoDB table exists for ECS
        run: |
          set -e
          TABLE="ecs-agents-jobs-state"
          echo "Checking DynamoDB table $TABLE..."
          if aws dynamodb describe-table --table-name "$TABLE" >/dev/null 2>&1; then
            echo "✓ DynamoDB table $TABLE already exists"
          else
            echo "Creating DynamoDB table $TABLE..."
            aws dynamodb create-table \
              --table-name "$TABLE" \
              --attribute-definitions AttributeName=id,AttributeType=S AttributeName=status,AttributeType=S \
              --key-schema AttributeName=id,KeyType=HASH \
              --billing-mode PAY_PER_REQUEST \
              --global-secondary-indexes 'IndexName=status-index,KeySchema=[{AttributeName=status,KeyType=HASH}],Projection={ProjectionType=ALL}'
            echo "Waiting for table to become ACTIVE..."
            aws dynamodb wait table-exists --table-name "$TABLE"
            echo "✓ DynamoDB table $TABLE created"
          fi

      - name: Get AWS account ID
        id: aws
        run: |
          ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT

      - name: Ensure ECR repository exists
        id: ecr
        env:
          ACCOUNT_ID: ${{ steps.aws.outputs.account_id }}
        run: |
          set -e
          REPO_NAME="__REPO_NAME__"
          AWS_REGION="${{ env.AWS_REGION }}"
          if aws ecr describe-repositories --repository-names "$REPO_NAME" >/dev/null 2>&1; then
            echo "✓ ECR repository exists"
          else
            aws ecr create-repository --repository-name "$REPO_NAME"
            echo "✓ Created ECR repository"
          fi
          REPO_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"
          echo "repo_uri=$REPO_URI" >> $GITHUB_OUTPUT

      - name: Login to ECR
        env:
          AWS_REGION: ${{ env.AWS_REGION }}
        run: |
          aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${{ steps.ecr.outputs.repo_uri }}"

      - name: Build and push Docker image
        env:
          REPO_URI: ${{ steps.ecr.outputs.repo_uri }}
        run: |
          IMAGE_TAG=${{ github.sha }}
          docker build -t "$REPO_URI:$IMAGE_TAG" -t "$REPO_URI:latest" .
          docker push "$REPO_URI:$IMAGE_TAG"
          docker push "$REPO_URI:latest"
          echo "image_uri=$REPO_URI:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Upload all secrets to SSM
        env:
          SECRETS_JSON: ${{ toJson(secrets) }}
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          echo "Uploading all repository secrets to SSM Parameter Store..."
          create_or_update_parameter() {
            local param_name="$1"
            local param_value="$2"
            local param_type="$3"
            if aws ssm put-parameter --name "$param_name" --value "$param_value" --type "$param_type" --no-overwrite 2>/dev/null; then
              echo "✓ Created new parameter: $param_name"
            else
              aws ssm put-parameter --name "$param_name" --value "$param_value" --type "$param_type" --overwrite
              echo "✓ Updated existing parameter: $param_name"
            fi
          }
          echo "$SECRETS_JSON" | jq -r 'to_entries[] | select(.key != "GITHUB_TOKEN") | @base64' | while read -r entry; do
            decoded=$(echo $entry | base64 --decode)
            key=$(echo $decoded | jq -r '.key')
            value=$(echo $decoded | jq -r '.value')
            if [ -n "$value" ] && [ "$value" != "null" ]; then
              if [[ $key == *"API_KEY"* ]] || [[ $key == *"TOKEN"* ]] || [[ $key == *"SECRET"* ]] || [[ $key == *"PASSWORD"* ]]; then
                param_type="SecureString"
              else
                param_type="String"
              fi
              param_name="/app/__REPO_NAME__/${ENVIRONMENT}/$key"
              create_or_update_parameter "$param_name" "$value" "$param_type"
            fi
          done

      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_wrapper: false

      - name: Terraform init + apply (ECS)
        env:
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          terraform -chdir=terraform init \
            -backend-config="region=eu-west-2" \
            -backend-config="bucket=533267084389-tf-state" \
            -backend-config="key=aws/$ENVIRONMENT/agents/__REPO_NAME__" \
            -backend-config="encrypt=true" \
            -backend-config="use_lockfile=true"

          # Handle cluster state for VPC changes
          CLUSTER_NAME="agents-$ENVIRONMENT"

          # Remove cluster from state if it exists (to handle VPC changes)
          if terraform -chdir=terraform state show "aws_ecs_cluster.shared_cluster[0]" >/dev/null 2>&1; then
            echo "Removing existing cluster from Terraform state due to infrastructure changes..."
            terraform -chdir=terraform state rm "aws_ecs_cluster.shared_cluster[0]"
          fi

          # Import cluster if it exists in AWS
          if aws ecs describe-clusters --clusters "$CLUSTER_NAME" --query 'clusters[?status==`ACTIVE`]' | grep -q "$CLUSTER_NAME"; then
            echo "✓ Shared cluster $CLUSTER_NAME exists, importing to Terraform state..."
            terraform -chdir=terraform import "aws_ecs_cluster.shared_cluster[0]" "$CLUSTER_NAME"
          else
            echo "Shared cluster $CLUSTER_NAME does not exist, Terraform will create it"
          fi

          terraform -chdir=terraform apply -auto-approve \
            -var="environment=$ENVIRONMENT" \
            -var="deployment_type=ecs" \
            -var="container_image=${{ steps.ecr.outputs.repo_uri }}:${{ github.sha }}" \
            -var="jobs_table_name=ecs-agents-jobs-state"

      - name: Show ECS endpoints
        run: |
          cd terraform
          
          # Get outputs
          ENVIRONMENT="${{ steps.env.outputs.environment }}"
          ALB_DNS=$(terraform output -raw ecs_alb_dns_name || echo "N/A")
          SERVICE_NAME=$(terraform output -raw ecs_service_name || echo "N/A")
          DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name || echo "N/A")
          HTTPS_URL=$(terraform output -raw ecs_https_url || echo "N/A")
          
          # Display deployment summary
          echo "============================================"
          echo "🚀 ECS Deployment Complete!"
          echo "============================================"
          echo ""
          echo "📌 Environment: $ENVIRONMENT"
          echo "📌 Service Name: $SERVICE_NAME"
          echo "📌 DynamoDB Table: $DYNAMODB_TABLE"
          echo "📌 ALB DNS: $ALB_DNS"
          echo ""
          echo "🌐 HTTPS URL: $HTTPS_URL"
          echo ""
          echo "============================================"
          
          # Also output as GitHub annotations (these might get masked but the above won't)
          echo "::notice title=Deployment Complete::Access your agent at $HTTPS_URL"
          
          # Create GitHub Step Summary (this appears in a separate section and won't be masked)
          echo "## 🚀 ECS Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | \`$ENVIRONMENT\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Service Name | \`$SERVICE_NAME\` |" >> $GITHUB_STEP_SUMMARY
          echo "| DynamoDB Table | \`$DYNAMODB_TABLE\` |" >> $GITHUB_STEP_SUMMARY
          echo "| ALB DNS | \`$ALB_DNS\` |" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### 🌐 Access Your Agent" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**HTTPS URL:** [$HTTPS_URL]($HTTPS_URL)" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "✅ Your agent is now deployed and accessible at the URL above." >> $GITHUB_STEP_SUMMARY
EOF

    echo "✓ Created ECS workflow file at .github/workflows/deploy.yml"
    # Replace placeholders and embed repo name in backend key
    if sed --version >/dev/null 2>&1; then
        sed -i -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
        sed -i -e "s#key=aws/\\$ENVIRONMENT/agents/\\$REPO_NAME#key=aws/\\$ENVIRONMENT/agents/$REPO_NAME#g" .github/workflows/deploy.yml
    else
        sed -i '' -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
        sed -i '' -e "s#key=aws/\\$ENVIRONMENT/agents/\\$REPO_NAME#key=aws/\\$ENVIRONMENT/agents/$REPO_NAME#g" .github/workflows/deploy.yml
    fi
}

# Function to create GitHub workflow file for Lambda ECR container deployment
create_github_workflow_lambda_ecr() {
    cat > ".github/workflows/deploy.yml" <<'EOF'
name: Deploy __REPO_NAME__ Lambda ECR Container

on:
  push:
    branches: [main, 'prod**']
  pull_request:
    branches: ['prod**']

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      TF_VAR_function_name: __REPO_NAME__
      TF_VAR_aws_region: eu-west-2
      TF_VAR_deployment_type: lambda-container
      TF_VAR_jobs_table_name: agents-jobs-state
      AWS_REGION: eu-west-2
    steps:
      - uses: actions/checkout@v4

      - name: Determine Environment
        id: env
        run: |
          if [[ "${{ github.ref }}" == "refs/heads/main" ]]; then
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (main branch)"
          elif [[ "${{ github.ref }}" == refs/heads/prod* ]]; then
            echo "environment=prod" >> $GITHUB_OUTPUT
            echo "Environment: prod (production branch)"
          else
            echo "environment=dev" >> $GITHUB_OUTPUT
            echo "Environment: dev (default)"
          fi

      - name: AWS credentials via OIDC
        uses: aws-actions/configure-aws-credentials@v3
        with:
          role-to-assume: arn:aws:iam::533267084389:role/github
          aws-region: eu-west-2

      - name: Get AWS account ID
        id: aws
        run: |
          ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
          echo "account_id=$ACCOUNT_ID" >> $GITHUB_OUTPUT

      - name: Ensure ECR repository exists
        id: ecr
        env:
          ACCOUNT_ID: ${{ steps.aws.outputs.account_id }}
        run: |
          set -e
          REPO_NAME="__REPO_NAME__"
          AWS_REGION="${{ env.AWS_REGION }}"
          if aws ecr describe-repositories --repository-names "$REPO_NAME" >/dev/null 2>&1; then
            echo "✓ ECR repository exists"
          else
            aws ecr create-repository --repository-name "$REPO_NAME"
            echo "✓ Created ECR repository"
          fi
          REPO_URI="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME"
          echo "repo_uri=$REPO_URI" >> $GITHUB_OUTPUT

      - name: Login to ECR
        env:
          AWS_REGION: ${{ env.AWS_REGION }}
        run: |
          aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${{ steps.ecr.outputs.repo_uri }}"

      - name: Build and push Docker image
        env:
          REPO_URI: ${{ steps.ecr.outputs.repo_uri }}
          IMAGE_TAG: ${{ github.sha }}
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          echo "Building Lambda container for environment: $ENVIRONMENT"

          # Build the Docker image using Lambda-specific Dockerfile
          docker build -f Dockerfile.lambda -t "$REPO_URI:$IMAGE_TAG" .

          # Tag with environment-specific tags
          docker tag "$REPO_URI:$IMAGE_TAG" "$REPO_URI:$ENVIRONMENT-$IMAGE_TAG"
          docker tag "$REPO_URI:$IMAGE_TAG" "$REPO_URI:$ENVIRONMENT-latest"

          # Push images to ECR with environment-specific tags
          echo "Pushing image to ECR with environment tags..."
          docker push "$REPO_URI:$IMAGE_TAG"
          docker push "$REPO_URI:$ENVIRONMENT-$IMAGE_TAG"
          docker push "$REPO_URI:$ENVIRONMENT-latest"

          # Also push latest for dev environment
          if [[ "$ENVIRONMENT" == "dev" ]]; then
            docker tag "$REPO_URI:$IMAGE_TAG" "$REPO_URI:latest"
            docker push "$REPO_URI:latest"
          fi

          echo "image_uri=$REPO_URI:$IMAGE_TAG" >> $GITHUB_OUTPUT

      - name: Upload all secrets to SSM
        env:
          SECRETS_JSON: ${{ toJson(secrets) }}
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          echo "Uploading all repository secrets to SSM Parameter Store..."
          create_or_update_parameter() {
            local param_name="$1"
            local param_value="$2"
            local param_type="$3"
            if aws ssm put-parameter --name "$param_name" --value "$param_value" --type "$param_type" --no-overwrite 2>/dev/null; then
              echo "✓ Created new parameter: $param_name"
            else
              aws ssm put-parameter --name "$param_name" --value "$param_value" --type "$param_type" --overwrite
              echo "✓ Updated existing parameter: $param_name"
            fi
          }
          echo "$SECRETS_JSON" | jq -r 'to_entries[] | select(.key != "GITHUB_TOKEN") | @base64' | while read -r entry; do
            decoded=$(echo $entry | base64 --decode)
            key=$(echo $decoded | jq -r '.key')
            value=$(echo $decoded | jq -r '.value')
            if [ -n "$value" ] && [ "$value" != "null" ]; then
              if [[ $key == *"API_KEY"* ]] || [[ $key == *"TOKEN"* ]] || [[ $key == *"SECRET"* ]] || [[ $key == *"PASSWORD"* ]]; then
                param_type="SecureString"
              else
                param_type="String"
              fi
              param_name="/app/__REPO_NAME__/${ENVIRONMENT}/$key"
              create_or_update_parameter "$param_name" "$value" "$param_type"
            fi
          done

      - name: Set up Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_wrapper: false

      - name: Terraform init + apply (Lambda Container)
        env:
          ENVIRONMENT: ${{ steps.env.outputs.environment }}
        run: |
          terraform -chdir=terraform init \
            -backend-config="region=eu-west-2" \
            -backend-config="bucket=533267084389-tf-state" \
            -backend-config="key=aws/$ENVIRONMENT/agents/__REPO_NAME__" \
            -backend-config="encrypt=true" \
            -backend-config="use_lockfile=true"

          terraform -chdir=terraform apply -auto-approve \
            -var="environment=$ENVIRONMENT" \
            -var="deployment_type=lambda-container" \
            -var="container_image=${{ steps.ecr.outputs.repo_uri }}:${{ github.sha }}" \
            -var="jobs_table_name=agents-jobs-state"

      - name: Show Lambda Container endpoints
        run: |
          cd terraform

          # Get outputs
          ENVIRONMENT="${{ steps.env.outputs.environment }}"
          FUNCTION_URL=$(terraform output -raw function_url || echo "N/A")
          FUNCTION_NAME=$(terraform output -raw function_name || echo "N/A")
          DYNAMODB_TABLE=$(terraform output -raw dynamodb_table_name || echo "N/A")

          # Display deployment summary
          echo "============================================"
          echo "🚀 Lambda Container Deployment Complete!"
          echo "============================================"
          echo ""
          echo "📌 Environment: $ENVIRONMENT"
          echo "📌 Function Name: $FUNCTION_NAME"
          echo "📌 DynamoDB Table: $DYNAMODB_TABLE"
          echo ""
          echo "🌐 Function URL: $FUNCTION_URL"
          echo ""
          echo "============================================"

          # Also output as GitHub annotations
          echo "::notice title=Deployment Complete::Access your Lambda function at $FUNCTION_URL"

          # Create GitHub Step Summary
          echo "## 🚀 Lambda Container Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Property | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|----------|-------|" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | \`$ENVIRONMENT\` |" >> $GITHUB_STEP_SUMMARY
          echo "| Function Name | \`$FUNCTION_NAME\` |" >> $GITHUB_STEP_SUMMARY
          echo "| DynamoDB Table | \`$DYNAMODB_TABLE\` |" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "### 🌐 Access Your Lambda Function" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "**Function URL:** [$FUNCTION_URL]($FUNCTION_URL)" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "✅ Your Lambda container function is now deployed and accessible at the URL above." >> $GITHUB_STEP_SUMMARY
EOF

    echo "✓ Created Lambda ECR workflow file at .github/workflows/deploy.yml"
    # Replace placeholders
    if sed --version >/dev/null 2>&1; then
        sed -i -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
    else
        sed -i '' -e "s/__REPO_NAME__/$REPO_NAME/g" .github/workflows/deploy.yml
    fi
}

# Function to set repository secrets (tries both methods)
set_repo_secrets() {
    echo "**"
    echo -e "\e[32mConfiguring GitHub Actions repository secrets...\e[0m"
    echo "**"

    # Wait a moment for repository to be fully created
    sleep 2

    # Try GitHub API first, fallback to gh CLI
    if set_repo_secrets_api; then
        echo -e "\e[32m✓ Successfully set all repository secrets via GitHub API\e[0m"
        return 0
    else
        echo -e "\e[33m⚠ GitHub API method failed, trying gh CLI...\e[0m"
        if set_repo_secrets_gh; then
            echo -e "\e[32m✓ Successfully set all repository secrets via gh CLI\e[0m"
            return 0
        else
            echo -e "\e[31m❌ Both secret setting methods failed\e[0m"
            echo -e "\e[33m⚠ You'll need to set repository secrets manually at:\e[0m"
            echo -e "\e[33m  https://github.com/$GITHUB_ORG/$REPO_NAME/settings/secrets/actions\e[0m"
            echo -e "\e[33m  Required secrets:\e[0m"
            echo -e "\e[33m    - APP_PORT: ${APP_PORT:-8000}\e[0m"
            echo -e "\e[33m    - APP_HOST: ${APP_HOST:-0.0.0.0}\e[0m"
            echo -e "\e[33m    - GH_TOKEN: [your GitHub token]\e[0m"
            echo -e "\e[33m    - ALLOW_ORIGINS: [cors origins]\e[0m"
            echo -e "\e[33m    - OPENAI_API_KEY: [your OpenAI key]\e[0m"
            echo -e "\e[33m    - AGENT_NAME: $AGENT_NAME\e[0m"
            echo -e "\e[33m    - AGENT_TYPE: $agent_type\e[0m"
            echo -e "\e[33m    - AGENT_EXECUTE_LIMIT: ${AGENT_EXECUTE_LIMIT:-1}\e[0m"
            return 1
        fi
    fi
}

# Function to reorganize directory structure
reorganize_directory_structure() {
    echo "Reorganizing directory structure..."

    # First, move the smart_agent directory if it exists in the temp clone
    if [ -d "$TEMP_CLONE_DIR/smart_agent" ]; then
        echo "Found smart_agent directory in blueprint..."

        # Remove existing PROJECT_NAME directory if it exists
        if [ -d "$PROJECT_NAME" ]; then
            rm -rf "$PROJECT_NAME"
        fi

        # Move the smart_agent contents
        mv "$TEMP_CLONE_DIR/smart_agent" "$PROJECT_NAME"
        echo -e "\e[32m✓ Moved smart_agent contents to $PROJECT_NAME/\e[0m"
    else
        echo -e "\e[31m❌ Warning: smart_agent directory not found in blueprint\e[0m"
    fi

    # Now move ALL other files and directories from temp clone to root level
    echo "Moving all other blueprint files and directories to root level..."

    # List what we're about to move (for debugging)
    echo "Files and directories in blueprint:"
    ls -la "$TEMP_CLONE_DIR/"

    # Move everything except smart_agent (which we already moved) and .git
    for item in "$TEMP_CLONE_DIR"/*; do
        if [ -e "$item" ]; then
            item_name=$(basename "$item")

            # Skip smart_agent (already moved) and .git directory
            if [ "$item_name" != "smart_agent" ] && [ "$item_name" != ".git" ]; then
                # If item already exists at root, remove it first
                if [ -e "$item_name" ]; then
                    rm -rf "$item_name"
                    echo -e "\e[33m✓ Removed existing $item_name\e[0m"
                fi

                # Move the item
                mv "$item" ./
                echo -e "\e[32m✓ Moved $item_name to root level\e[0m"
            fi
        fi
    done

    # Also move hidden files (like .gitignore, .env files, etc.) but not .git
    for item in "$TEMP_CLONE_DIR"/.*; do
        if [ -e "$item" ]; then
            item_name=$(basename "$item")

            # Skip . and .. and .git directories
            if [ "$item_name" != "." ] && [ "$item_name" != ".." ] && [ "$item_name" != ".git" ]; then
                # If item already exists at root, remove it first
                if [ -e "$item_name" ]; then
                    rm -rf "$item_name"
                    echo -e "\e[33m✓ Removed existing $item_name\e[0m"
                fi

                # Move the item
                mv "$item" ./
                echo -e "\e[32m✓ Moved hidden file $item_name to root level\e[0m"
            fi
        fi
    done

    # Clean up temp directory
    rm -rf "$TEMP_CLONE_DIR"
    echo -e "\e[32m✓ Cleaned up temporary clone directory\e[0m"

    # Verify the structure is correct
    echo -e "\n\e[32mFinal project structure:\e[0m"
    ls -la ./

    if [ -d "$PROJECT_NAME/src" ]; then
        echo -e "\e[32m✓ Directory structure verified - $PROJECT_NAME/ folder with src/ inside\e[0m"
    else
        echo -e "\e[31m❌ Warning: Expected src/ directory not found in $PROJECT_NAME/\e[0m"
    fi

    # Check for lambda_handler.py at root level
    if [ -f "lambda_handler.py" ]; then
        echo -e "\e[32m✓ Found lambda_handler.py at root level\e[0m"
    else
        echo -e "\e[33m⚠ lambda_handler.py not found at root level (may not be in blueprint)\e[0m"
    fi

    # Check for lambda_handler.py in smart_agent
    if [ -f "$PROJECT_NAME/lambda_handler.py" ]; then
        echo -e "\e[32m✓ Found lambda_handler.py inside $PROJECT_NAME/\e[0m"
    else
        echo -e "\e[33m⚠ lambda_handler.py not found inside $PROJECT_NAME/ (may not be in blueprint)\e[0m"
    fi
}

# Function to clean up agent files based on selected type
cleanup_agent_files() {
    local agent_dir="$PROJECT_NAME/src/agent"
    local config_dir="$PROJECT_NAME/src/config"
    local controllers_dir="$PROJECT_NAME/src/controllers"

    echo "Cleaning up unused agent files for type: $agent_type"

    # Remove unused agent type files
    all_agent_types=("general" "gimlet" "mojito" "daiquiri" "oldFashioned")

    for type in "${all_agent_types[@]}"; do
        if [ "$type" != "$agent_type" ]; then
            # Remove unused files from agent directory
            if [ -f "$agent_dir/base_agent_${type}.py" ]; then
                rm "$agent_dir/base_agent_${type}.py"
                echo -e "\e[31m- Removed base_agent_${type}.py\e[0m"
            fi

            # Remove unused files from config directory
            if [ -f "$config_dir/agent_${type}.json" ]; then
                rm "$config_dir/agent_${type}.json"
                echo -e "\e[31m- Removed agent_${type}.json\e[0m"
            fi

            # Remove unused files from controllers directory
            if [ -f "$controllers_dir/ExecuteController_${type}.py" ]; then
                rm "$controllers_dir/ExecuteController_${type}.py"
                echo -e "\e[31m- Removed ExecuteController_${type}.py\e[0m"
            fi
        fi
    done

    # Rename selected agent files to standard names (only if not general)
    if [ "$agent_type" != "general" ]; then
        if [ -f "$agent_dir/base_agent_${agent_type}.py" ]; then
            mv "$agent_dir/base_agent_${agent_type}.py" "$agent_dir/base_agent.py"
            echo -e "\e[32m✓ Renamed base_agent_${agent_type}.py to base_agent.py\e[0m"
        fi

        if [ -f "$config_dir/agent_${agent_type}.json" ]; then
            mv "$config_dir/agent_${agent_type}.json" "$config_dir/agent.json"
            echo -e "\e[32m✓ Renamed agent_${agent_type}.json to agent.json\e[0m"
        fi

        if [ -f "$controllers_dir/ExecuteController_${agent_type}.py" ]; then
            mv "$controllers_dir/ExecuteController_${agent_type}.py" "$controllers_dir/ExecuteController.py"
            echo -e "\e[32m✓ Renamed ExecuteController_${agent_type}.py to ExecuteController.py\e[0m"
        fi
    else
        echo -e "\e[32m✓ Using general agent type (default files)\e[0m"
    fi
}

# Function to remove sensitive data from files before git operations
sanitize_files_for_git() {
    echo "Sanitizing files for git commit..."

    # Create a temporary sanitized version of setup.sh for git
    cp setup.sh setup.sh.backup

    # Replace any potential token values with placeholder
    if sed --version >/dev/null 2>&1; then
        # GNU sed
        sed -i -E 's/ghp_[A-Za-z0-9_]+/GH_TOKEN_PLACEHOLDER/g' setup.sh
        sed -i -E 's/sk-[A-Za-z0-9_]+/OPENAI_API_KEY_PLACEHOLDER/g' setup.sh
    else
        # BSD/macOS sed
        sed -i '' -E 's/ghp_[A-Za-z0-9_]+/GH_TOKEN_PLACEHOLDER/g' setup.sh
        sed -i '' -E 's/sk-[A-Za-z0-9_]+/OPENAI_API_KEY_PLACEHOLDER/g' setup.sh
    fi

    echo -e "\e[32m✓ Files sanitized for git commit\e[0m"
}

# Function to restore files after git operations
restore_files_after_git() {
    echo "Restoring original files..."

    if [ -f "setup.sh.backup" ]; then
        mv setup.sh.backup setup.sh
        echo -e "\e[32m✓ Original files restored\e[0m"
    fi
}

# Function to initialize new git repository and push to remote
initialize_new_git_repo() {
    echo "**"
    echo -e "\e[32mInitializing new git repository...\e[0m"
    echo "**"

    # Ensure we're actually inside a git repo; do not trust .git folder existence alone
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo -e "\e[32m✓ Git repository detected\e[0m"
    else
        rm -rf .git 2>/dev/null || true
        git init -b main 2>/dev/null || { git init && git branch -M main; }
        if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
            echo -e "\e[32m✓ Initialized new git repository\e[0m"
        else
            echo -e "\e[31m❌ Failed to initialize git repository\e[0m"
            return 1
        fi
    fi

    # Set git user config if not already set
    if ! git config --get user.email > /dev/null 2>&1; then
        git config user.email "github-actions@github.com"
        git config user.name "GitHub Actions"
        echo -e "\e[32m✓ Set git user configuration\e[0m"
    fi

    # Ensure non-interactive git operations in diverse environments
    # - Disable GPG signing to avoid pinentry prompts
    # - Disable hooks to avoid custom pre-commit/push hooks hanging
    # - Disable background gc that may stall on large trees
    git config --local commit.gpgsign false || true
    git config --local core.hooksPath /dev/null || true
    git config --local gc.auto 0 || true

    # Configure remote origin (create or update)
    if git remote get-url origin >/dev/null 2>&1; then
        git remote set-url origin "https://$GH_TOKEN:x-oauth-basic@github.com/$GITHUB_ORG/$REPO_NAME.git" || return 1
        echo -e "\e[32m✓ Updated remote origin\e[0m"
    else
        git remote add origin "https://$GH_TOKEN:x-oauth-basic@github.com/$GITHUB_ORG/$REPO_NAME.git" || return 1
        echo -e "\e[32m✓ Added remote origin\e[0m"
    fi

    # Create .gitignore
    cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
pip-log.txt
pip-delete-this-directory.txt
.pytest_cache/
.coverage
htmlcov/
.tox/
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Logs
logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Dependency directories
node_modules/

# Terraform
*.tfstate
*.tfstate.*
.terraform/
.terraform.lock.hcl

# AWS Lambda
deployment.zip
lambda_layer.zip
package/

# Replit
.replit
.upm/
.pythonlibs/
replit.nix
pyproject.toml
poetry.lock

# Local development
.pytest_cache/
.mypy_cache/
dist/
build/
*.egg-info/

# Temporary files
blueprint_temp/

# Backup files
*.backup
EOF

    echo -e "\e[32m✓ Created .gitignore\e[0m"

    # Sanitize files before git operations
    sanitize_files_for_git

    # Stage all files
    git add -A || return 1
    echo -e "\e[32m✓ Staged all files\e[0m"

    # Create initial commit (only if there are changes)
    if ! git diff --cached --quiet; then
      git commit --no-gpg-sign -m "Initial commit: $AGENT_NAME ($agent_type agent type)

- Generated from oneForAll blueprint
- Agent type: $agent_type
- Project structure: single smart_agent/ folder
- External folders: .github, scripts, terraform
- Root level files: lambda_handler.py and others
- S3 deployment configuration with latest-only storage
- Shared DynamoDB table for job state (agents-jobs-state)"
      echo -e "\e[32m✓ Created initial commit\e[0m"
    else
      echo -e "\e[33mNo changes to commit\e[0m"
    fi

    # Ensure we are on main branch
    git branch -M main || git checkout -B main || return 1
    echo -e "\e[32m✓ On main branch\e[0m"

    # Push to remote repository
    echo -e "\e[32mPushing to remote repository...\e[0m"
    if git -c core.hooksPath=/dev/null push -u origin main; then
        echo -e "\e[32m✓ Successfully pushed to remote repository\e[0m"
        echo -e "\e[32m🔗 Repository: https://github.com/$GITHUB_ORG/$REPO_NAME\e[0m"
    else
        echo -e "\e[31m❌ Failed to push to remote repository\e[0m"
        echo -e "\e[33m⚠ You can push manually later with: git push -u origin main\e[0m"
    fi

    # Restore original files
    restore_files_after_git
}

# Function to create the lambda packaging script
create_lambda_package_script() {
    mkdir -p scripts
    cat > scripts/package-lambda.py << 'EOF'
import os
import shutil
from pathlib import Path

def create_lambda_package():
    """Create Lambda deployment package"""
    print("Creating Lambda deployment package...")
    
    PACKAGE_DIR = Path("package")
    
    # Clean up existing package directory
    if PACKAGE_DIR.exists():
        shutil.rmtree(PACKAGE_DIR)
    
    PACKAGE_DIR.mkdir()
    
    # Install dependencies
    print("Installing dependencies...")
    os.system(f"pip install -r smart_agent/requirements.txt -t {PACKAGE_DIR}")
    
    # Copy source code
    print("Copying source code...")
    shutil.copytree("smart_agent", PACKAGE_DIR / "smart_agent")
    shutil.copy("lambda_handler.py", PACKAGE_DIR / "lambda_handler.py")
    
    # Copy the Prompt directory if it exists
    if Path("Prompt").exists():
        print("Copying Prompt directory...")
        shutil.copytree("Prompt", PACKAGE_DIR / "Prompt")
    
    # Create deployment zip
    print("Creating deployment package...")
    shutil.make_archive("deployment", "zip", PACKAGE_DIR)
    
    # Get package size
    package_size = os.path.getsize("deployment.zip")
    package_size_mb = package_size / (1024 * 1024)
    
    print(f"Package created: deployment.zip ({package_size_mb:.2f} MB)")
    
    # Clean up package directory
    shutil.rmtree(PACKAGE_DIR)
    
    return package_size_mb

if __name__ == "__main__":
    size = create_lambda_package()
    print(f"Lambda package ready: {size:.2f} MB")
EOF

    echo -e "\e[32m✓ Created Lambda packaging script\e[0m"
}

# Function to create Dockerfile.lambda for ECR Lambda deployments
create_dockerfile_lambda() {
    cat > "Dockerfile.lambda" <<'EOF'
# AWS Lambda Python runtime
FROM public.ecr.aws/lambda/python:3.11

# Install system dependencies if needed
RUN yum update -y && \
    yum install -y \
        unzip \
        wget \
        curl \
        gcc \
        gcc-c++ \
        make \
        openssl-devel \
        libffi-devel \
        python3-devel && \
    yum clean all && \
    rm -rf /var/cache/yum

# Copy requirements and install Python dependencies
COPY smart_agent/requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

# Copy application code
COPY smart_agent/ ${LAMBDA_TASK_ROOT}/smart_agent/
COPY lambda_handler.py ${LAMBDA_TASK_ROOT}/

# Set the Lambda handler
CMD ["lambda_handler.handler"]
EOF

    echo -e "\e[32m✓ Created Dockerfile.lambda for ECR Lambda deployment\e[0m"
}

# Function to create updated terraform main.tf
create_terraform_config() {
    mkdir -p terraform
    cat > terraform/main.tf << 'EOF'
########################################
#            Terraform Block           #
########################################
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    region         = "eu-west-2"
    bucket         = "533267084389-tf-state"
    key            = "aws/${var.environment}/agents/${var.function_name}"
    encrypt        = true
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

########################################
#            Input Variables           #
########################################
variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "deployment_type" {
  description = "Deployment target: 'lambda', 'lambda-container', or 'ecs'"
  type        = string
  default     = "lambda"
}

variable "s3_bucket" {
  description = "S3 bucket containing the deployment package"
  type        = string
  default     = ""
}

variable "s3_key" {
  description = "S3 key for the deployment package"
  type        = string
  default     = ""
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-2"
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "jobs_table_name" {
  description = "Name of the shared DynamoDB table for agent job state"
  type        = string
  default     = "agents-jobs-state"
}

# ECS and Lambda Container variables
variable "container_image" {
  description = "Full container image URI (ECR) for ECS or Lambda container deployment"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID to deploy ECS service into (defaults to default VPC)"
  type        = string
  default     = ""
}

  variable "public_subnet_ids" {
    description = "Public subnet IDs for the ECS service (defaults to default VPC public subnets)"
    type        = list(string)
    default     = []
  }


locals {
  is_lambda           = var.deployment_type == "lambda"
  is_lambda_container = var.deployment_type == "lambda-container"
  is_ecs              = var.deployment_type == "ecs"
  is_any_lambda       = local.is_lambda || local.is_lambda_container
}

########################################
#         Shared DynamoDB Table        #
########################################
# Look up an existing, shared jobs table by name. It must exist and expose
# a GSI named "status-index" on the attribute "status" for efficient queries.
data "aws_dynamodb_table" "jobs" {
  name = var.jobs_table_name
}

########################################
#        Existing Resources (Data)     #
########################################
# Look-up S3 bucket - managed by GitHub Actions (Lambda ZIP only)
data "aws_s3_bucket" "lambda_artifacts" {
  count  = local.is_lambda ? 1 : 0
  bucket = var.s3_bucket
}

# Get the S3 object to track changes (Lambda ZIP only)
data "aws_s3_object" "lambda_package" {
  count  = local.is_lambda ? 1 : 0
  bucket = var.s3_bucket
  key    = var.s3_key
}

# Default VPC and public subnets (Lambda only, or ECS fallback if no shared ALB)
data "aws_vpc" "default" {
  count   = local.is_any_lambda && var.vpc_id == "" ? 1 : 0
  default = true
}

data "aws_subnets" "default_public" {
  count = local.is_any_lambda && length(var.public_subnet_ids) == 0 ? 1 : 0
  filter {
    name   = "default-for-az"
    values = ["true"]
  }
}

data "aws_caller_identity" "current" {}

########################################
#         Lambda IAM Role & Policy     #
########################################
resource "aws_iam_role" "lambda_exec" {
  count = local.is_any_lambda ? 1 : 0
  name  = "${var.function_name}-${var.environment}-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Action    = "sts:AssumeRole",
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })

  tags = {
    Name        = "${var.function_name}-${var.environment}-exec"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_role_policy_attachment" "basic" {
  count      = local.is_any_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "dynamodb_rw" {
  name = "${var.function_name}-${var.environment}-dynamodb-rw"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect   = "Allow",
      Action   = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:DeleteItem",
        "dynamodb:UpdateItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:DescribeTable"
      ],
      Resource = [
        data.aws_dynamodb_table.jobs.arn,
        "${data.aws_dynamodb_table.jobs.arn}/index/*"
      ]
    }]
  })

  tags = {
    Name        = "${var.function_name}-${var.environment}-dynamodb-rw"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_policy" "ssm_parameter_read" {
  name = "${var.function_name}-${var.environment}-ssm-parameter-read"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
        "ssm:GetParameter",
        "ssm:GetParameters",
        "ssm:GetParametersByPath",
        "ssm:DescribeParameters"
      ],
      Resource = [
        "arn:aws:ssm:${var.aws_region}:*:parameter/app/${var.function_name}/${var.environment}",
        "arn:aws:ssm:${var.aws_region}:*:parameter/app/${var.function_name}/${var.environment}/*"
      ]
    }]
  })

  tags = {
    Name        = "${var.function_name}-${var.environment}-ssm-parameter-read"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_rw" {
  count      = local.is_any_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = aws_iam_policy.dynamodb_rw.arn
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_read" {
  count      = local.is_any_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = aws_iam_policy.ssm_parameter_read.arn
}

########################################
#            Lambda Function           #
########################################
# Lambda function with ZIP deployment (traditional)
resource "aws_lambda_function" "agent_zip" {
  count            = local.is_lambda ? 1 : 0
  function_name    = "${var.function_name}-${var.environment}"
  s3_bucket        = var.s3_bucket
  s3_key           = var.s3_key
  source_code_hash = data.aws_s3_object.lambda_package[0].etag
  role             = aws_iam_role.lambda_exec[0].arn
  handler          = "lambda_handler.handler"
  runtime          = "python3.11"
  timeout          = 900
  memory_size      = 2048

  environment {
    variables = {
      JOB_TABLE        = var.jobs_table_name
      PARAMETER_PREFIX = "/app/${var.function_name}/${var.environment}"
      ENVIRONMENT      = var.environment
    }
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Lambda function with container deployment (ECR)
resource "aws_lambda_function" "agent_container" {
  count         = local.is_lambda_container ? 1 : 0
  function_name = "${var.function_name}-${var.environment}"
  role          = aws_iam_role.lambda_exec[0].arn
  package_type  = "Image"
  image_uri     = var.container_image
  timeout       = 900
  memory_size   = 2048

  environment {
    variables = {
      JOB_TABLE        = var.jobs_table_name
      PARAMETER_PREFIX = "/app/${var.function_name}/${var.environment}"
      ENVIRONMENT      = var.environment
    }
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Lambda Function URL for ZIP deployment
resource "aws_lambda_function_url" "agent_zip_url" {
  count              = local.is_lambda ? 1 : 0
  function_name      = aws_lambda_function.agent_zip[0].function_name
  authorization_type = "NONE"
}

# Lambda Function URL for container deployment
resource "aws_lambda_function_url" "agent_container_url" {
  count              = local.is_lambda_container ? 1 : 0
  function_name      = aws_lambda_function.agent_container[0].function_name
  authorization_type = "NONE"
}

# Lambda permissions for ZIP deployment function URL
# Required for AWS Lambda function URL authorization model (Nov 1, 2026 compliance)
resource "aws_lambda_permission" "agent_zip_url_invoke_url" {
  count                  = local.is_lambda ? 1 : 0
  statement_id           = "FunctionURLAllowPublicAccess-InvokeURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.agent_zip[0].function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "agent_zip_url_invoke_function" {
  count         = local.is_lambda ? 1 : 0
  statement_id  = "FunctionURLAllowPublicAccess-InvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent_zip[0].function_name
  principal     = "*"
}

# Lambda permissions for Container deployment function URL
# Required for AWS Lambda function URL authorization model (Nov 1, 2026 compliance)
resource "aws_lambda_permission" "agent_container_url_invoke_url" {
  count                  = local.is_lambda_container ? 1 : 0
  statement_id           = "FunctionURLAllowPublicAccess-InvokeURL"
  action                 = "lambda:InvokeFunctionUrl"
  function_name          = aws_lambda_function.agent_container[0].function_name
  principal              = "*"
  function_url_auth_type = "NONE"
}

resource "aws_lambda_permission" "agent_container_url_invoke_function" {
  count         = local.is_lambda_container ? 1 : 0
  statement_id  = "FunctionURLAllowPublicAccess-InvokeFunction"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent_container[0].function_name
  principal     = "*"
}


########################################
#                ECS (Fargate)         #
########################################

// ECR repository is created/managed by the GitHub Action to avoid
// state conflicts when it already exists. Terraform does not manage ECR here.

resource "aws_iam_role" "ecs_task_execution" {
  count = local.is_ecs ? 1 : 0
  name  = "${var.function_name}-${var.environment}-ecs-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_exec_attach" {
  count      = local.is_ecs ? 1 : 0
  role       = aws_iam_role.ecs_task_execution[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy_attachment" "ecs_exec_ssm" {
  count      = local.is_ecs ? 1 : 0
  role       = aws_iam_role.ecs_task_execution[0].name
  policy_arn = aws_iam_policy.ssm_parameter_read.arn
}

resource "aws_iam_role" "ecs_task" {
  count = local.is_ecs ? 1 : 0
  name  = "${var.function_name}-${var.environment}-ecs-task"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_task_dynamodb" {
  count      = local.is_ecs ? 1 : 0
  role       = aws_iam_role.ecs_task[0].name
  policy_arn = aws_iam_policy.dynamodb_rw.arn
}

resource "aws_iam_role_policy_attachment" "ecs_task_ssm" {
  count      = local.is_ecs ? 1 : 0
  role       = aws_iam_role.ecs_task[0].name
  policy_arn = aws_iam_policy.ssm_parameter_read.arn
}

locals {
  # Use the same VPC as the shared ALB for ECS deployment (ai-news-dev-alb)
  shared_vpc_id = "vpc-0ee84a9c32768e901"
  effective_vpc_id = local.is_ecs ? local.shared_vpc_id : (var.vpc_id != "" ? var.vpc_id : (local.is_any_lambda ? data.aws_vpc.default[0].id : ""))
  effective_public_subnets = local.is_ecs ? data.aws_subnets.shared_vpc_public[0].ids : (length(var.public_subnet_ids) > 0 ? var.public_subnet_ids : (local.is_any_lambda ? data.aws_subnets.default_public[0].ids : []))
}

# Get security groups from the shared ALB
data "aws_security_groups" "shared_alb_sgs" {
  count = local.is_ecs ? 1 : 0
  filter {
    name   = "group-id"
    values = data.aws_lb.shared_alb[0].security_groups
  }
}

resource "aws_security_group" "service_sg" {
  count  = local.is_ecs ? 1 : 0
  name   = "${var.function_name}-${var.environment}-svc-sg"
  vpc_id = local.shared_vpc_id

  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = data.aws_lb.shared_alb[0].security_groups
  }
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}-svc-sg"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Agent       = var.function_name
  }
}

# Use existing shared load balancer instead of creating individual ALBs
data "aws_lb" "shared_alb" {
  count = local.is_ecs ? 1 : 0
  arn   = "arn:aws:elasticloadbalancing:eu-west-2:533267084389:loadbalancer/app/ai-news-dev-alb/5e29f03dbbed36e1"
}

# Get public subnets from the shared VPC
data "aws_subnets" "shared_vpc_public" {
  count = local.is_ecs ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [local.shared_vpc_id]
  }
  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

resource "aws_lb_target_group" "ecs_tg" {
  count       = local.is_ecs ? 1 : 0
  name        = "${var.function_name}-${var.environment}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = local.shared_vpc_id
  target_type = "ip"
  
  # Keep connections alive during long-running tasks
  deregistration_delay = 300  # 5 minutes (default)
  
  # Enable stickiness to keep sessions on the same target
  stickiness {
    type            = "lb_cookie"
    enabled         = true
    cookie_duration = 86400  # 24 hours
  }

  lifecycle {
    create_before_destroy = true
  }
  health_check {
    path                = "/discover"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
    matcher             = "200"
  }
}

# Get existing HTTPS listener from shared ALB
data "aws_lb_listener" "shared_https" {
  count             = local.is_ecs ? 1 : 0
  load_balancer_arn = data.aws_lb.shared_alb[0].arn
  port              = 443
}

# Create HTTPS listener rule for host-based routing to this agent
resource "aws_lb_listener_rule" "agent_rule" {
  count        = local.is_ecs ? 1 : 0
  listener_arn = data.aws_lb_listener.shared_https[0].arn
  priority     = 100 + abs(parseint(substr(sha256("${var.function_name}-${var.environment}"), 0, 4), 16)) % 900

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg[0].arn
  }

  condition {
    host_header {
      values = ["${var.function_name}-${var.environment}.activate.bar"]
    }
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}-rule"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Agent       = var.function_name
  }
}

# Route53 zone lookup for activate.bar domain
data "aws_route53_zone" "activate_bar" {
  count        = local.is_ecs ? 1 : 0
  name         = "activate.bar"
  private_zone = false
}

# Create Route53 A record for the agent subdomain
resource "aws_route53_record" "agent_subdomain" {
  count   = local.is_ecs ? 1 : 0
  zone_id = data.aws_route53_zone.activate_bar[0].zone_id
  name    = "${var.function_name}-${var.environment}.activate.bar"
  type    = "A"

  alias {
    name                   = data.aws_lb.shared_alb[0].dns_name
    zone_id                = data.aws_lb.shared_alb[0].zone_id
    evaluate_target_health = false
  }

  depends_on = [aws_lb_listener_rule.agent_rule]
}

# Shared ECS clusters - use shared cluster names
locals {
  shared_cluster_name = var.environment == "prod" ? "agents-prod" : "agents-dev"
}

# Import existing cluster or create new one
# If cluster exists: terraform import aws_ecs_cluster.shared_cluster[0] <cluster-name>
# If not exists: terraform will create it
resource "aws_ecs_cluster" "shared_cluster" {
  count = local.is_ecs ? 1 : 0
  name  = local.shared_cluster_name

  tags = {
    Name        = local.shared_cluster_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Purpose     = "SharedAgentCluster"
  }
}

locals {
  cluster_id = local.is_ecs ? aws_ecs_cluster.shared_cluster[0].id : ""
}

resource "aws_cloudwatch_log_group" "ecs" {
  count             = local.is_ecs ? 1 : 0
  name              = "/ecs/${var.function_name}-${var.environment}"
  retention_in_days = 14
}

resource "aws_ecs_task_definition" "task" {
  count                    = local.is_ecs ? 1 : 0
  family                   = "${var.function_name}-${var.environment}"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "512"
  memory                   = "1024"
  execution_role_arn       = aws_iam_role.ecs_task_execution[0].arn
  task_role_arn            = aws_iam_role.ecs_task[0].arn

  container_definitions = jsonencode([
    {
      name      = "${var.function_name}"
      image     = var.container_image
      essential = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      environment = [
        { name = "JOB_TABLE",        value = var.jobs_table_name },
        { name = "ENVIRONMENT",      value = var.environment },
        { name = "PARAMETER_PREFIX", value = "/app/${var.function_name}/${var.environment}" }
      ]
      secrets = [
        { name = "APP_PORT",             valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/APP_PORT" },
        { name = "APP_HOST",             valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/APP_HOST" },
        { name = "ALLOW_ORIGINS",       valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/ALLOW_ORIGINS" },
        { name = "OPENAI_API_KEY",      valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/OPENAI_API_KEY" },
        { name = "AGENT_NAME",          valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/AGENT_NAME" },
        { name = "AGENT_TYPE",          valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/AGENT_TYPE" },
        { name = "AGENT_EXECUTE_LIMIT", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/AGENT_EXECUTE_LIMIT" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.ecs[0].name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:8000/status || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 5
      }
    }
  ])
}

resource "aws_ecs_service" "service" {
  count           = local.is_ecs ? 1 : 0
  name            = "${var.function_name}-${var.environment}"
  cluster         = local.cluster_id
  task_definition = aws_ecs_task_definition.task[0].arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = local.effective_public_subnets
    security_groups  = [aws_security_group.service_sg[0].id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.ecs_tg[0].arn
    container_name   = var.function_name
    container_port   = 8000
  }

  depends_on = [aws_lb_listener_rule.agent_rule]
}

########################################
#               Outputs                #
########################################

output "function_url" {
  value = local.is_lambda ? aws_lambda_function_url.agent_zip_url[0].function_url : (local.is_lambda_container ? aws_lambda_function_url.agent_container_url[0].function_url : null)
  description = "Lambda function URL"
}

output "function_name" {
  value = local.is_lambda ? aws_lambda_function.agent_zip[0].function_name : (local.is_lambda_container ? aws_lambda_function.agent_container[0].function_name : null)
  description = "Full Lambda function name with environment (Lambda)"
}

output "dynamodb_table_name" {
  value       = data.aws_dynamodb_table.jobs.name
  description = "Shared DynamoDB table name for agent jobs"
}

output "dynamodb_table_arn" {
  value       = data.aws_dynamodb_table.jobs.arn
  description = "Shared DynamoDB table ARN for agent jobs"
}

output "parameter_prefix" {
  value = "/app/${var.function_name}/${var.environment}"
  description = "SSM Parameter prefix where all secrets are stored"
}

output "s3_bucket" {
  value       = local.is_lambda ? data.aws_s3_bucket.lambda_artifacts[0].bucket : null
  description = "S3 bucket for Lambda ZIP artifacts (not used for container deployments)"
}

output "s3_key" {
  value = var.s3_key
  description = "S3 key for the deployment package"
}

output "environment" {
  value = var.environment
  description = "Deployment environment"
}

output "ssm_parameter_info" {
  value = {
    parameter_prefix = "/app/${var.function_name}/${var.environment}"
    description     = "All GitHub repository secrets are automatically uploaded to SSM Parameter Store under this prefix"
    access_pattern  = "Lambda reads parameters using PARAMETER_PREFIX environment variable"
  }
}

output "dynamodb_info" {
  value = {
    table_name  = data.aws_dynamodb_table.jobs.name
    table_arn   = data.aws_dynamodb_table.jobs.arn
    hash_key    = "id"
    gsi_name    = "status-index"
    description = "Shared DynamoDB table for job state across multiple agents"
  }
}

output "ecs_alb_dns_name" {
  value       = local.is_ecs ? data.aws_lb.shared_alb[0].dns_name : null
  description = "Public DNS name of the shared ALB (ECS only)"
}

  output "ecs_service_name" {
    value       = local.is_ecs ? aws_ecs_service.service[0].name : null
    description = "ECS service name (ECS only)"
  }
  
  output "ecs_https_url" {
    value       = local.is_ecs ? "https://${var.function_name}-${var.environment}.activate.bar" : null
    description = "Full HTTPS URL for the ECS service with environment-aware subdomain"
  }
EOF

    echo -e "\e[32m✓ Created Terraform configuration with shared DynamoDB table\e[0m"
}

# Check if this is a setup run or a regular run
if [ "$1" == "setup" ] || [ ! -d "$PROJECT_NAME" ]; then
    # SETUP MODE
    echo "**"
    echo -e "\e[32mInfo- Starting setup for '$AGENT_NAME' ($agent_type type)\e[0m"
    echo -e "\e[32mGitHub Repository: $REPO_NAME\e[0m"
    echo -e "\e[32mLocal Folder: $PROJECT_NAME\e[0m"
    echo -e "\e[32mS3 Deployment: Latest-only package storage\e[0m"
    echo -e "\e[32mDynamoDB: Shared table for job state (agents-jobs-state)\e[0m"
    echo "**"
    echo -e "\n"

    # Create .env file for local development
    echo "Creating .env file for local development..."
    cat > .env << EOF
APP_PORT=${APP_PORT:-8000}
APP_HOST=${APP_HOST:-0.0.0.0}
ALLOW_ORIGINS=${ALLOW_ORIGINS:-http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar}
OPENAI_API_KEY=${OPENAI_API_KEY}
GH_TOKEN=${GH_TOKEN}
AGENT_NAME=${AGENT_NAME}
AGENT_TYPE=${agent_type}
AGENT_EXECUTE_LIMIT=${AGENT_EXECUTE_LIMIT:-1}
EOF

    # Check required environment variables
    echo "Checking environment variables..."
    missing_vars=()

    required_vars=("GH_TOKEN" "OPENAI_API_KEY")

    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        else
            echo -e "\e[32m✓ Found $var\e[0m"
        fi
    done

    # If missing variables, prompt user to input them
    if [ ${#missing_vars[@]} -gt 0 ]; then
        if ! prompt_missing_variables "${missing_vars[@]}"; then
            echo "**"
            echo -e "\e[31m❌ Setup cannot continue without required environment variables\e[0m"
            echo -e "\e[33m💡 Alternative: Set these variables in your environment:\e[0m"
            for var in "${missing_vars[@]}"; do
                echo -e "\e[33m   export $var=\"your_value_here\"\e[0m"
            done
            echo "**"
            exit 1
        fi
        
        # Update the .env file with the new values
        echo "Updating .env file with provided values..."
        cat > .env << EOF
APP_PORT=${APP_PORT:-8000}
APP_HOST=${APP_HOST:-0.0.0.0}
ALLOW_ORIGINS=${ALLOW_ORIGINS:-http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar}
OPENAI_API_KEY=${OPENAI_API_KEY}
GH_TOKEN=${GH_TOKEN}
AGENT_NAME=${AGENT_NAME}
AGENT_TYPE=${agent_type}
AGENT_EXECUTE_LIMIT=${AGENT_EXECUTE_LIMIT:-1}
EOF
        echo -e "\e[32m✓ Environment file updated with provided values\e[0m"
        
        # Update the BLUEPRINT_REPO_URL with the new GH_TOKEN
        BLUEPRINT_REPO_URL="https://$GH_TOKEN:x-oauth-basic@github.com/Activate-Intelligence/agent-blueprint.git"
    fi

    # Create new GitHub repository
    create_github_repo_with_readme

    # Clone the blueprint repository to a temporary directory
    echo "Downloading blueprint..."

    if [ -d "$TEMP_CLONE_DIR" ]; then
        echo "Removing existing temporary directory..."
        rm -rf "$TEMP_CLONE_DIR"
    fi

    if [ -d "$PROJECT_NAME" ]; then
        echo "Removing existing $PROJECT_NAME folder..."
        rm -rf "$PROJECT_NAME"
    fi

    git clone --branch main "$BLUEPRINT_REPO_URL" "$TEMP_CLONE_DIR" || {
        echo -e "\e[31m❌ Failed to clone blueprint repository\e[0m"
        exit 1
    }

    echo -e "\e[32m✓ Blueprint downloaded\e[0m"

    # Reorganize directory structure
    reorganize_directory_structure

    echo "**"
    echo -e "\e[32mConfiguring agent type: $agent_type for '$AGENT_NAME'\e[0m"
    echo "**"

    # Clean up unused agent files
    cleanup_agent_files

    # Create .env.sample for the project
    cat > "$PROJECT_NAME/.env.sample" << EOF
# Environment Configuration Template
# Copy this file to .env and fill in your actual values
# DO NOT commit the .env file - it contains secrets!

APP_PORT=8000
APP_HOST=0.0.0.0
ALLOW_ORIGINS=http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar
OPENAI_API_KEY=sk-proj-YOUR_OPENAI_API_KEY_HERE
AGENT_NAME=$AGENT_NAME
AGENT_TYPE=$agent_type
GH_TOKEN=ghp_YOUR_GITHUB_TOKEN_HERE
AGENT_EXECUTE_LIMIT=1
EOF

    # Clean up requirements.txt
    if [ -f "$PROJECT_NAME/requirements.txt" ]; then
        # Remove duplicates and ensure consistent casing
        sort "$PROJECT_NAME/requirements.txt" | uniq > "$PROJECT_NAME/requirements_tmp.txt"
        mv "$PROJECT_NAME/requirements_tmp.txt" "$PROJECT_NAME/requirements.txt"
        echo -e "\e[32m✓ Cleaned up requirements.txt\e[0m"
    fi

    # Create terraform configuration
    create_terraform_config

    # Create .github/workflows directory
    mkdir -p ".github/workflows"

    # Create GitHub workflow file based on deploy_target
    if [ "$deploy_target" = "ecs" ]; then
        create_github_workflow_ecs
    elif [ "$deploy_target" = "lambda_ecr" ]; then
        create_github_workflow_lambda_ecr
    else
        create_github_workflow
    fi

    # Create scripts directory and lambda packaging script
    create_lambda_package_script

    # Create Dockerfile.lambda if lambda_ecr is selected
    if [ "$deploy_target" = "lambda_ecr" ]; then
        create_dockerfile_lambda
    fi

    # Create README.md for the local repository
    cat > README.md << EOF
# $AGENT_NAME

This is a custom AI agent built using the oneForAll blueprint framework with optimized S3-based Lambda deployment and a shared DynamoDB table.

## Agent Configuration
- **Agent Name**: $AGENT_NAME
- **Agent Type**: $agent_type
- **Repository**: $REPO_NAME
- **Deployment**: S3-based Lambda deployment (latest-only storage)
- **Database**: Shared DynamoDB table for job state (agents-jobs-state)

## Description
$AGENT_NAME is an AI agent designed to help with various tasks using the $agent_type configuration.

## Deployment Architecture
- **S3 Bucket**: 533267084389-lambda-artifacts
- **Storage Strategy**: Latest package only (automatic cleanup)
- **Structure**: $REPO_NAME/dev/ and $REPO_NAME/prod/
- **Environment Logic**: 
  - main branch → dev environment
  - prod* branches → prod environment
- **DynamoDB**: Shared jobs table (agents-jobs-state) with status-index GSI

## Development Guidelines

### Prerequisites
- python3 >= 3.11.3
- fastapi >= 0.70.0
- uvicorn >= 0.15.0

### Technology Stack
- FastAPI
- Uvicorn
- Poetry
- AWS Lambda (S3 deployment)
- DynamoDB (shared jobs table)
- Terraform

### Setup Instructions

\`\`\`bash
# Step 1: Clone this repository
git clone https://github.com/$GITHUB_ORG/$REPO_NAME.git
cd $REPO_NAME

# Step 2: Create a .env file with your configuration
cat > .env << 'ENV_EOF'
APP_PORT=8000
APP_HOST=0.0.0.0
ALLOW_ORIGINS=http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar
OPENAI_API_KEY=your_openai_api_key_here
AGENT_NAME=$AGENT_NAME
AGENT_TYPE=$agent_type
GH_TOKEN=your_github_token_here
AGENT_EXECUTE_LIMIT=1
ENV_EOF

# Step 3: Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r smart_agent/requirements.txt

# Step 4: Run the agent locally
cd smart_agent
python3 main.py
# OR
uvicorn main:app --reload
\`\`\`

## Project Structure

\`\`\`
$REPO_NAME/
├── .github/workflows/     # GitHub Actions CI/CD (S3 deployment)
├── scripts/              # Build and deployment scripts
│   └── package-lambda.py # Lambda packaging script
├── terraform/            # Infrastructure as Code (S3-based + DynamoDB)
├── smart_agent/          # Main application code
│   ├── src/
│   │   ├── agent/        # Agent implementation
│   │   ├── config/       # Configuration files
│   │   └── controllers/  # API controllers
│   ├── main.py           # Application entry point
│   ├── requirements.txt  # Python dependencies
│   └── .env.sample       # Environment template
├── lambda_handler.py     # AWS Lambda handler (root level)
├── .env                  # Environment variables (local)
├── .gitignore           # Git ignore rules
└── README.md            # This file
\`\`\`

## Deployment Information

### S3 Deployment Strategy
- **Latest-Only Storage**: Only the most recent deployment package is stored
- **Automatic Cleanup**: Old packages are automatically deleted before new uploads
- **Consistent Naming**: Uses \`deployment-latest.zip\` for easy identification
- **Metadata Tracking**: Includes deployment timestamp, git SHA, and environment info

### DynamoDB Strategy
- **Shared Jobs Table**: All agents write to a single table per account
- **Default Name**: \`agents-jobs-state\` (override with `TF_VAR_jobs_table_name`)
- **Global Secondary Index**: \`status-index\` on attribute `status` for efficient queries
- **Job IDs**: Provided by the frontend and globally unique

### S3 Structure
\`\`\`
533267084389-lambda-artifacts/
├── $REPO_NAME/
│   ├── dev/
│   │   └── deployment-latest.zip
│   └── prod/
│       └── deployment-latest.zip
\`\`\`

### DynamoDB Structure
\`\`\`
agents-jobs-state      # Shared across agents and environments
\`\`\`

### Environment Management
- **Development**: Triggered by pushes to main branch
- **Production**: Triggered by pushes to prod* branches
- **SSM Parameters**: Environment-specific parameter paths
- **Resource Isolation**: Environment-specific IAM roles and policies (DynamoDB table is shared)

### AWS Resources
- Lambda function with S3 deployment
- API Gateway for HTTP endpoints
- Shared DynamoDB table for job state
- SSM Parameter Store for secrets
- S3 bucket for deployment artifacts

## API Documentation
Once running, visit: http://localhost:8000/docs

## Built with oneForAll Blueprint
This agent was generated using the oneForAll blueprint system with optimized S3 deployment and a shared DynamoDB table.
- Blueprint Repository: https://github.com/Activate-Intelligence/oneForAll_blueprint_Lambda
- Generated on: $(date)
- S3 Deployment: Latest-only storage optimization
- DynamoDB: Shared table used across agents
EOF

    # Create .replit configuration
    cat > .replit << EOL
run = "bash setup.sh run"
language = "python3"
modules = ["python-3.11:v18-20230807-322e88b", "python-3.11:v25-20230920-d4ad2e4"]
hidden = [".pythonlibs", "venv", ".config", "**/pycache", "**/.mypy_cache", "**/*.pyc"]

[env]
VIRTUAL_ENV = "/home/runner/\${REPL_SLUG}/venv"
PATH = "\${VIRTUAL_ENV}/bin:\${PATH}"
PYTHONPATH = "\${REPL_HOME}"
APP_PORT = "${APP_PORT:-8000}"
APP_HOST = "${APP_HOST:-0.0.0.0}"
ALLOW_ORIGINS = "${ALLOW_ORIGINS:-http://localhost:9000,http://localhost:3000,https://api.dev.spritz.cafe,https://api.spritz.cafe,https://app.dev.spritz.cafe,https://app.spritz.cafe,https://api.dev.spritz.activate.bar,https://api.spritz.activate.bar,https://app.dev.spritz.activate.bar,https://spritz.activate.bar}"
OPENAI_API_KEY = "${OPENAI_API_KEY}"
GH_TOKEN = "${GH_TOKEN}"
AGENT_NAME = "${AGENT_NAME}"
AGENT_TYPE = "${agent_type}"
AGENT_EXECUTE_LIMIT = "${AGENT_EXECUTE_LIMIT:-1}"

[debugger]
support = true

[packager]
language = "python3"
ignoredPackages = ["unit_tests"]

[languages]
[languages.python3]
pattern = "**/*.py"
[languages.python3.languageServer]
start = "pylsp"

[deployment]
run = ["sh", "-c", "bash setup.sh run"]
deploymentTarget = "gce"

[[ports]]
localPort = ${APP_PORT:-8000}
externalPort = 80
EOL

    # Setup Python environment
    echo "**"
    echo -e "\e[32mSetting up Python environment...\e[0m"
    echo "**"

    # Disable forced --user installs that cause issues in Replit
    export PIP_USER=0
    unset PYTHONUSERBASE

    # Create virtual environment
    if [ ! -d "venv" ]; then
        python3 -m venv venv
        echo "✓ Created virtual environment"
    fi

    # Activate virtual environment
    source venv/bin/activate
    echo "✓ Activated virtual environment"

    # Install dependencies
    echo "Installing dependencies..."

    # Upgrade pip first
    pip install --upgrade pip --no-user

    # Install dependencies from requirements.txt
    if [ -f "$PROJECT_NAME/requirements.txt" ]; then
        echo "Installing from $PROJECT_NAME/requirements.txt..."
        pip install --no-user -r "$PROJECT_NAME/requirements.txt"
        echo "✓ Dependencies installed successfully"
    else
        echo "requirements.txt not found. Installing basic dependencies..."
        pip install --no-user fastapi uvicorn openai pydantic python-dotenv
        echo "✓ Basic dependencies installed"
    fi

    # Verify critical packages are installed
    echo "Verifying installation..."
    python -c "import uvicorn, fastapi; print('✓ FastAPI and Uvicorn ready')" || {
        echo "❌ Installation verification failed"
        echo "Attempting to fix..."
        pip install --no-user fastapi uvicorn
    }

    # Set repository secrets AFTER the repository is created and pushed
    set_repo_secrets

    # Initialize new git repository and push to remote
    initialize_new_git_repo

    echo "**"
    echo -e "\e[32m🎉 Setup completed successfully!\e[0m"
    echo -e "\e[32m📁 Agent Name: $AGENT_NAME\e[0m"
    echo -e "\e[32m🔧 Agent Type: $agent_type\e[0m"
    echo -e "\e[32m📂 Local Folder: $PROJECT_NAME/\e[0m"
    echo -e "\e[32m📂 GitHub Repository: https://github.com/$GITHUB_ORG/$REPO_NAME\e[0m"
    echo -e "\e[32m🔗 Repository pushed to: https://github.com/$GITHUB_ORG/$REPO_NAME.git\e[0m"
    
    if [ "$deploy_target" = "ecs" ]; then
        echo -e "\e[32m🌐 HTTPS URL: https://$REPO_NAME.activate.bar\e[0m"
        echo -e "\e[33m⚠️  Note: The HTTPS URL will be available after the GitHub Actions workflow completes the deployment.\e[0m"
    fi
    echo -e "\e[32m🔐 Repository secrets configured for GitHub Actions\e[0m"
    echo -e "\e[32m☁️  S3 Deployment: Latest-only storage (533267084389-lambda-artifacts)\e[0m"
    echo -e "\e[32m🗄️  DynamoDB: Shared table (agents-jobs-state)\e[0m"
    echo -e "\e[32m🧹 Auto-cleanup: Old packages automatically removed\e[0m"
    echo -e "\e[32m🌍 Environment Logic: main→dev, prod*→prod\e[0m"
    echo -e "\e[32m▶️  Ready to run! Click the Run button or use: bash setup.sh run\e[0m"
    echo "**"
    echo -e "\e[32m✓ All files pushed to GitHub automatically\e[0m"
    echo -e "\e[32m✓ Repository secrets configured for CI/CD\e[0m"
    echo -e "\e[32m✓ S3-based Lambda deployment with latest-only storage\e[0m"
    echo -e "\e[32m✓ Shared DynamoDB jobs table (status-index GSI)\e[0m"
    echo -e "\e[32m✓ Environment-specific resources to prevent conflicts\e[0m"
    echo "**"

else
    # RUN MODE
    echo "**"
    echo -e "\e[32mPreparing to run the agent...\e[0m"
    echo "**"

    # Load environment variables first
    if [ -f ".env" ]; then
        export $(grep -v '^#' .env | xargs)
        echo "Loaded environment variables from .env"
    fi

    # Disable forced --user installs for Replit compatibility
    export PIP_USER=0
    unset PYTHONUSERBASE

    # Ensure virtual environment exists and is activated
    if [ ! -d "venv" ]; then
        echo "Virtual environment not found. Creating..."
        python3 -m venv venv
    fi

    # Activate virtual environment
    source venv/bin/activate
    echo "✓ Activated virtual environment"

    # Check if dependencies are installed, install if missing
    if ! python -c "import uvicorn" 2>/dev/null; then
        echo "Dependencies missing. Installing..."
        pip install --upgrade pip --no-user

        if [ -f "$PROJECT_NAME/requirements.txt" ]; then
            pip install --no-user -r "$PROJECT_NAME/requirements.txt"
            echo "✓ Installed dependencies from $PROJECT_NAME/requirements.txt"
        else
            echo "requirements.txt not found. Installing basic dependencies..."
            pip install --no-user fastapi uvicorn openai pydantic python-dotenv
        fi
    else
        echo "✓ Dependencies are already installed"
    fi

    # Verify installation
    echo "Verifying installation..."
    python -c "import uvicorn, fastapi; print('✓ FastAPI and Uvicorn are ready')" || {
        echo "❌ Installation verification failed"
        echo "Attempting emergency install..."
        pip install --no-user --force-reinstall fastapi uvicorn
        exit 1
    }

    echo "**"
    echo -e "\e[32mStarting ${AGENT_NAME:-Agent} (${AGENT_TYPE:-general} type)...\e[0m"
    echo -e "\e[32mS3 Deployment: Latest-only storage enabled\e[0m"
    echo -e "\e[32mDynamoDB: Shared table enabled\e[0m"
    echo "**"

    # Set Python path and run the application
    export PYTHONPATH="${REPL_HOME}:${PYTHONPATH}"
    cd "$PROJECT_NAME"

    echo "Starting server on http://0.0.0.0:${APP_PORT:-8000}"
    echo "API documentation will be available at: http://0.0.0.0:${APP_PORT:-8000}/docs"
    echo ""

    python3 main.py

fi
```
