########################################
#            Terraform Block           #
########################################
terraform {
  required_version = ">= 1.5.0"

  backend "s3" {
    region         = "eu-west-2"
    bucket         = "533267084389-tf-state"
    key            = "aws/${var.environment}/agents/${var.function_name}"
    dynamodb_table = "533267084389-tf-lock"
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
  description = "Deployment target: 'lambda' or 'ecs'"
  type        = string
  default     = "lambda"
  validation {
    condition     = contains(["lambda", "ecs"], var.deployment_type)
    error_message = "deployment_type must be 'lambda' or 'ecs'."
  }
}

variable "s3_bucket" {
  description = "S3 bucket containing the deployment package"
  type        = string
}

variable "s3_key" {
  description = "S3 key for the deployment package"
  type        = string
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

# ECS-specific inputs
variable "container_image" {
  description = "Full ECR image URI for ECS deployment"
  type        = string
  default     = ""
}

variable "vpc_id" {
  description = "VPC ID to deploy ECS resources into (defaults to default VPC)"
  type        = string
  default     = ""
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for ECS service (defaults to default VPC public subnets)"
  type        = list(string)
  default     = []
}

# HTTPS and domain configuration for ECS via ALB
variable "root_domain" {
  description = "Root DNS domain hosted in Route53 (e.g., activate.bar)"
  type        = string
  default     = "activate.bar"
}

variable "enable_https" {
  description = "Enable HTTPS and Route53 records for ECS ALB"
  type        = bool
  default     = true
}

variable "existing_cert_arn" {
  description = "Optional existing ACM certificate ARN to use for the subdomain"
  type        = string
  default     = ""
}

locals {
  is_lambda = var.deployment_type == "lambda"
  is_ecs    = var.deployment_type == "ecs"
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
# Look-up S3 bucket - managed by GitHub Actions (lambda only)
data "aws_s3_bucket" "lambda_artifacts" {
  count  = local.is_lambda ? 1 : 0
  bucket = var.s3_bucket
}

# Get the S3 object to track changes (lambda only)
data "aws_s3_object" "lambda_package" {
  count  = local.is_lambda ? 1 : 0
  bucket = var.s3_bucket
  key    = var.s3_key
}

# Default VPC/subnets for ECS when not provided
data "aws_vpc" "default" {
  count   = local.is_ecs && var.vpc_id == "" ? 1 : 0
  default = true
}

data "aws_subnets" "default_public" {
  count = local.is_ecs && length(var.public_subnet_ids) == 0 ? 1 : 0
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
  count = local.is_lambda ? 1 : 0
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
  count      = local.is_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "dynamodb_rw" {
  name = "${var.function_name}-${var.environment}-dynamodb-rw"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect = "Allow",
      Action = [
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
  count      = local.is_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = aws_iam_policy.dynamodb_rw.arn
}

resource "aws_iam_role_policy_attachment" "lambda_ssm_read" {
  count      = local.is_lambda ? 1 : 0
  role       = aws_iam_role.lambda_exec[0].name
  policy_arn = aws_iam_policy.ssm_parameter_read.arn
}

########################################
#            Lambda Function           #
########################################
resource "aws_lambda_function" "agent" {
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

resource "aws_lambda_function_url" "agent_url" {
  count              = local.is_lambda ? 1 : 0
  function_name      = aws_lambda_function.agent[0].function_name
  authorization_type = "NONE"
}

########################################
#         API Gateway (optional)       #
########################################
resource "aws_apigatewayv2_api" "agent" {
  count         = local.is_lambda ? 1 : 0
  name          = "${var.function_name}-${var.environment}-api"
  protocol_type = "HTTP"

  tags = {
    Name        = "${var.function_name}-${var.environment}-api"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  count                  = local.is_lambda ? 1 : 0
  api_id                 = aws_apigatewayv2_api.agent[0].id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.agent[0].invoke_arn
  payload_format_version = "2.0"
}

locals {
  routes = [
    { path = "/abort", method = "GET" },
    { path = "/discover", method = "GET" },
    { path = "/docs", method = "GET" },
    { path = "/execute", method = "POST" },
    { path = "/log/{filename}", method = "GET" },
    { path = "/openapi.json", method = "ANY" },
    { path = "/status", method = "GET" },
  ]
}

resource "aws_lambda_permission" "apigw" {
  for_each = local.is_lambda ? { for r in local.routes : "${r.method}${r.path}" => r } : {}

  statement_id  = "AllowAPIGatewayInvoke-${var.environment}-${replace(replace(replace(replace(replace(each.key, "/", "-"), "{", "-"), "}", "-"), " ", "-"), ".", "-")}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.agent[0].arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.agent[0].execution_arn}/*/${each.value.method}${each.value.path}"
}

resource "aws_apigatewayv2_route" "routes" {
  for_each  = local.is_lambda ? { for r in local.routes : "${r.method} ${r.path}" => r } : {}
  api_id    = aws_apigatewayv2_api.agent[0].id
  route_key = "${each.value.method} ${each.value.path}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda[0].id}"
}

resource "aws_apigatewayv2_stage" "default" {
  count       = local.is_lambda ? 1 : 0
  api_id      = aws_apigatewayv2_api.agent[0].id
  name        = "$default"
  auto_deploy = true

  tags = {
    Name        = "${var.function_name}-${var.environment}-stage"
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

########################################
#                ECS (Fargate)         #
########################################

// ECR repository is created/managed outside Terraform (GitHub Actions step).
// This avoids conflicts when the repository already exists.

resource "aws_iam_role" "ecs_task_execution" {
  count = local.is_ecs ? 1 : 0
  name  = "${var.function_name}-${var.environment}-ecs-exec"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
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
      Effect    = "Allow",
      Principal = { Service = "ecs-tasks.amazonaws.com" },
      Action    = "sts:AssumeRole"
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
  effective_vpc_id         = var.vpc_id != "" ? var.vpc_id : (local.is_ecs ? data.aws_vpc.default[0].id : "")
  effective_public_subnets = length(var.public_subnet_ids) > 0 ? var.public_subnet_ids : (local.is_ecs ? data.aws_subnets.default_public[0].ids : [])
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
  vpc_id = data.aws_lb.shared_alb[0].vpc_id

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
  arn   = "arn:aws:elasticloadbalancing:eu-west-2:533267084389:loadbalancer/app/activate-bar-alb/beae142041799a98"
}

resource "aws_lb_target_group" "ecs_tg" {
  count       = local.is_ecs ? 1 : 0
  name        = "${var.function_name}-${var.environment}-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = data.aws_lb.shared_alb[0].vpc_id
  target_type = "ip"

  # Keep connections alive during long-running tasks
  deregistration_delay = 300 # 5 minutes (default)

  # Enable stickiness to keep sessions on the same target
  stickiness {
    type            = "lb_cookie"
    enabled         = true
    cookie_duration = 86400 # 24 hours
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}-tg"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Agent       = var.function_name
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

# Get existing HTTP listener from shared ALB
data "aws_lb_listener" "shared_http" {
  count             = local.is_ecs ? 1 : 0
  load_balancer_arn = data.aws_lb.shared_alb[0].arn
  port              = 80
}

# Create listener rule to route traffic to this agent
resource "aws_lb_listener_rule" "agent_rule" {
  count        = local.is_ecs ? 1 : 0
  listener_arn = data.aws_lb_listener.shared_http[0].arn
  priority     = 100 + abs(parseint(substr(sha256(var.function_name), 0, 4), 16)) % 900 # Generate unique priority from function name hash

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg[0].arn
  }

  condition {
    path_pattern {
      values = ["/${var.function_name}-${var.environment}/*"]
    }
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}-rule"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Agent       = var.function_name
  }
}

# Get existing HTTPS listener from shared ALB (if it exists)
data "aws_lb_listener" "shared_https" {
  count             = local.is_ecs ? 1 : 0
  load_balancer_arn = data.aws_lb.shared_alb[0].arn
  port              = 443
}

# Create HTTPS listener rule to route traffic to this agent
resource "aws_lb_listener_rule" "agent_https_rule" {
  count        = local.is_ecs ? 1 : 0
  listener_arn = data.aws_lb_listener.shared_https[0].arn
  priority     = 100 + abs(parseint(substr(sha256(var.function_name), 0, 4), 16)) % 900 # Generate unique priority from function name hash

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.ecs_tg[0].arn
  }

  condition {
    path_pattern {
      values = ["/${var.function_name}-${var.environment}/*"]
    }
  }

  tags = {
    Name        = "${var.function_name}-${var.environment}-https-rule"
    Environment = var.environment
    ManagedBy   = "Terraform"
    Agent       = var.function_name
  }
}

# Note: Agents are now accessible via the shared ALB at:
# HTTP: http://activate-bar-alb-90191003.eu-west-2.elb.amazonaws.com/{agent_name}-{environment}/*
# HTTPS: https://activate-bar-alb-90191003.eu-west-2.elb.amazonaws.com/{agent_name}-{environment}/* (if HTTPS listener exists)
# This allows both dev and prod versions of the same agent to run simultaneously

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
      name         = "${var.function_name}"
      image        = var.container_image
      essential    = true
      portMappings = [{ containerPort = 8000, protocol = "tcp" }]
      environment = [
        { name = "JOB_TABLE", value = var.jobs_table_name },
        { name = "ENVIRONMENT", value = var.environment },
        { name = "PARAMETER_PREFIX", value = "/app/${var.function_name}/${var.environment}" }
      ]
      secrets = [
        { name = "APP_PORT", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/APP_PORT" },
        { name = "APP_HOST", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/APP_HOST" },
        { name = "ALLOW_ORIGINS", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/ALLOW_ORIGINS" },
        { name = "OPENAI_API_KEY", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/OPENAI_API_KEY" },
        { name = "AGENT_NAME", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/AGENT_NAME" },
        { name = "AGENT_TYPE", valueFrom = "arn:aws:ssm:${var.aws_region}:${data.aws_caller_identity.current.account_id}:parameter/app/${var.function_name}/${var.environment}/AGENT_TYPE" },
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
output "api_endpoint" {
  value       = local.is_lambda ? aws_apigatewayv2_stage.default[0].invoke_url : null
  description = "API Gateway endpoint URL"
}

output "function_url" {
  value       = local.is_lambda ? aws_lambda_function_url.agent_url[0].function_url : null
  description = "Lambda function URL"
}

output "function_name" {
  value       = local.is_lambda ? aws_lambda_function.agent[0].function_name : null
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
  value       = "/app/${var.function_name}/${var.environment}"
  description = "SSM Parameter prefix where all secrets are stored"
}

output "s3_bucket" {
  value       = local.is_lambda ? data.aws_s3_bucket.lambda_artifacts[0].bucket : null
  description = "S3 bucket for Lambda artifacts"
}

output "s3_key" {
  value       = var.s3_key
  description = "S3 key for the deployment package"
}

output "environment" {
  value       = var.environment
  description = "Deployment environment"
}

output "ssm_parameter_info" {
  value = {
    parameter_prefix = "/app/${var.function_name}/${var.environment}"
    description      = "All GitHub repository secrets are automatically uploaded to SSM Parameter Store under this prefix"
    access_pattern   = "Lambda reads parameters using PARAMETER_PREFIX environment variable"
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

output "ecs_http_url" {
  value       = local.is_ecs ? "http://${data.aws_lb.shared_alb[0].dns_name}/${var.function_name}-${var.environment}" : null
  description = "HTTP URL for the ECS service via shared ALB"
}

output "ecs_https_url" {
  value       = local.is_ecs ? "https://${data.aws_lb.shared_alb[0].dns_name}/${var.function_name}-${var.environment}" : null
  description = "HTTPS URL for the ECS service via shared ALB"
}
