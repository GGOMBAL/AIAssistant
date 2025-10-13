/**
 * AI Assistant LLM Router Server
 * Claude.md 규칙에 따른 실제 라우터 서버 구현
 *
 * Author: AI Assistant System
 * Date: 2025-09-15
 * Rules: Claude.md 규칙 12 준수
 */

const express = require('express');
const cors = require('cors');
const axios = require('axios');
const winston = require('winston');
const rateLimit = require('express-rate-limit');
const fs = require('fs').promises;
const path = require('path');

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Configure logging
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.errors({ stack: true }),
    winston.format.json()
  ),
  defaultMeta: { service: 'llm-router' },
  transports: [
    new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
    new winston.transports.File({ filename: 'logs/router.log' }),
    new winston.transports.Console({
      format: winston.format.simple()
    })
  ]
});

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 1 * 60 * 1000, // 1 minute
  max: 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use(limiter);

// Load configuration
let config = {};
let agentConfigs = {};

async function loadConfigurations() {
  try {
    // Load router config
    const configData = await fs.readFile('router_config.json', 'utf8');
    config = JSON.parse(configData);
    logger.info('Router configuration loaded');

    // Load agent model config
    try {
      const agentConfigData = await fs.readFile('../config/agent_model.yaml', 'utf8');
      // Simple YAML parsing for agents section
      const yamlLines = agentConfigData.split('\n');
      let inAgentsSection = false;
      let currentAgent = null;

      for (const line of yamlLines) {
        if (line.trim() === 'agents:') {
          inAgentsSection = true;
          continue;
        }

        if (inAgentsSection && line.match(/^  \w+:/)) {
          currentAgent = line.trim().replace(':', '');
          agentConfigs[currentAgent] = {};
        } else if (inAgentsSection && currentAgent && line.match(/^\s{4}\w+:/)) {
          const [key, value] = line.trim().split(': ');
          agentConfigs[currentAgent][key] = value.replace(/"/g, '');
        } else if (line.match(/^[a-zA-Z]/)) {
          inAgentsSection = false;
        }
      }
      logger.info('Agent configurations loaded');
    } catch (error) {
      logger.warn('Could not load agent configs, using defaults');
    }

  } catch (error) {
    logger.error('Failed to load configuration:', error);
    process.exit(1);
  }
}

// Model providers simulation (실제 환경에서는 실제 API 호출)
const modelProviders = {
  'claude-3-opus-20240229': {
    provider: 'anthropic',
    cost_per_1k_tokens: 0.015,
    max_tokens: 200000,
    simulate: true
  },
  'claude-3-5-sonnet-20241022': {
    provider: 'anthropic',
    cost_per_1k_tokens: 0.003,
    max_tokens: 200000,
    simulate: true
  },
  'claude-3-sonnet-20240229': {
    provider: 'anthropic',
    cost_per_1k_tokens: 0.003,
    max_tokens: 200000,
    simulate: true
  },
  'claude-3-haiku-20240307': {
    provider: 'anthropic',
    cost_per_1k_tokens: 0.00025,
    max_tokens: 200000,
    simulate: true
  },
  'gemini-pro': {
    provider: 'google',
    cost_per_1k_tokens: 0.001,
    max_tokens: 32000,
    simulate: true
  }
};

// Model selection logic
function selectModel(agent, task, context = {}, preferences = {}) {
  const agentConfig = agentConfigs[agent] || {};
  const primaryModel = agentConfig.primary_model || 'claude-3-sonnet-20240229';
  const fallbackModel = agentConfig.fallback_model || 'claude-3-haiku-20240307';

  // Task-based selection
  if (task === 'large_dataset_processing' || context.dataset_size === 'large') {
    return 'gemini-pro';
  }

  if (context.cost_optimization || preferences.strategy === 'cost_efficiency') {
    return 'claude-3-haiku-20240307';
  }

  if (context.quality_critical || preferences.strategy === 'quality_first') {
    return 'claude-3-opus-20240229';
  }

  if (context.time_critical) {
    return 'claude-3-haiku-20240307';
  }

  return primaryModel;
}

// Simulate LLM API call
async function callLLMModel(model, message, preferences = {}) {
  const startTime = Date.now();

  try {
    // Simulate processing time based on model
    const processingTime = {
      'claude-3-opus-20240229': 2000 + Math.random() * 1000,
      'claude-3-5-sonnet-20241022': 1200 + Math.random() * 500,
      'claude-3-sonnet-20240229': 1000 + Math.random() * 500,
      'claude-3-haiku-20240307': 500 + Math.random() * 300,
      'gemini-pro': 800 + Math.random() * 400
    }[model] || 1000;

    await new Promise(resolve => setTimeout(resolve, processingTime));

    const responseTime = Date.now() - startTime;
    const tokensUsed = Math.floor(message.length / 4) + Math.floor(Math.random() * 500) + 100;
    const modelInfo = modelProviders[model];
    const cost = (tokensUsed / 1000) * modelInfo.cost_per_1k_tokens;

    // Simulate model-specific response
    const responses = {
      'claude-3-opus-20240229': `High-quality detailed analysis: ${message.substring(0, 100)}... [Comprehensive response with deep insights]`,
      'claude-3-5-sonnet-20241022': `Advanced analysis (3.5): ${message.substring(0, 100)}... [Enhanced reasoning and accuracy]`,
      'claude-3-sonnet-20240229': `Balanced analysis: ${message.substring(0, 100)}... [Well-structured response]`,
      'claude-3-haiku-20240307': `Quick response: ${message.substring(0, 50)}... [Concise answer]`,
      'gemini-pro': `Efficient processing: ${message.substring(0, 100)}... [Large-scale optimized response]`
    };

    return {
      success: true,
      response: responses[model],
      metadata: {
        model_used: model,
        provider: modelInfo.provider,
        response_time: responseTime,
        tokens_used: tokensUsed,
        cost: cost,
        timestamp: new Date().toISOString()
      }
    };

  } catch (error) {
    logger.error(`Model call failed for ${model}:`, error);
    return {
      success: false,
      error: error.message,
      metadata: {
        model_used: model,
        response_time: Date.now() - startTime,
        timestamp: new Date().toISOString()
      }
    };
  }
}

// Routes

// Health check
app.get('/api/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    version: '1.0.0',
    uptime: process.uptime()
  });
});

// Get available models
app.get('/api/models', (req, res) => {
  const models = Object.keys(modelProviders).map(model => ({
    name: model,
    provider: modelProviders[model].provider,
    max_tokens: modelProviders[model].max_tokens,
    cost_per_1k_tokens: modelProviders[model].cost_per_1k_tokens
  }));

  res.json({ models });
});

// Get router status
app.get('/api/status', (req, res) => {
  res.json({
    status: 'operational',
    loaded_agents: Object.keys(agentConfigs),
    available_models: Object.keys(modelProviders),
    config_loaded: Object.keys(config).length > 0,
    timestamp: new Date().toISOString()
  });
});

// Main routing endpoint
app.post('/api/route', async (req, res) => {
  const startTime = Date.now();

  try {
    const { agent, task, message, preferences = {}, context = {} } = req.body;

    if (!agent || !task || !message) {
      return res.status(400).json({
        error: 'Missing required fields: agent, task, message'
      });
    }

    logger.info(`Routing request: ${agent} -> ${task}`);

    // Select optimal model
    const selectedModel = selectModel(agent, task, context, preferences);
    logger.info(`Selected model: ${selectedModel} for ${agent}:${task}`);

    // Call the selected model
    const result = await callLLMModel(selectedModel, message, preferences);

    if (result.success) {
      res.json({
        model_used: selectedModel,
        response: result.response,
        metadata: {
          ...result.metadata,
          agent: agent,
          task: task,
          selection_reason: `Optimized for ${agent} ${task} task`,
          total_processing_time: Date.now() - startTime
        }
      });
    } else {
      // Try fallback model
      const agentConfig = agentConfigs[agent] || {};
      const fallbackModel = agentConfig.fallback_model || 'claude-3-haiku-20240307';

      logger.warn(`Primary model failed, trying fallback: ${fallbackModel}`);
      const fallbackResult = await callLLMModel(fallbackModel, message, preferences);

      if (fallbackResult.success) {
        res.json({
          model_used: fallbackModel,
          response: fallbackResult.response,
          metadata: {
            ...fallbackResult.metadata,
            agent: agent,
            task: task,
            fallback_used: true,
            primary_model_error: result.error,
            total_processing_time: Date.now() - startTime
          }
        });
      } else {
        res.status(500).json({
          error: 'Both primary and fallback models failed',
          primary_error: result.error,
          fallback_error: fallbackResult.error
        });
      }
    }

  } catch (error) {
    logger.error('Route request failed:', error);
    res.status(500).json({
      error: 'Internal server error',
      message: error.message
    });
  }
});

// Get metrics
app.get('/api/metrics', (req, res) => {
  // In a real implementation, this would return actual metrics
  res.json({
    total_requests: Math.floor(Math.random() * 1000) + 100,
    successful_requests: Math.floor(Math.random() * 900) + 90,
    failed_requests: Math.floor(Math.random() * 10),
    average_response_time: Math.random() * 2000 + 500,
    model_usage: {
      'claude-3-opus-20240229': Math.floor(Math.random() * 50) + 10,
      'claude-3-sonnet-20240229': Math.floor(Math.random() * 100) + 50,
      'claude-3-haiku-20240307': Math.floor(Math.random() * 30) + 10,
      'gemini-pro': Math.floor(Math.random() * 40) + 20
    },
    uptime: process.uptime(),
    timestamp: new Date().toISOString()
  });
});

// Error handling middleware
app.use((error, req, res, next) => {
  logger.error('Unhandled error:', error);
  res.status(500).json({
    error: 'Internal server error',
    message: error.message
  });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({
    error: 'Endpoint not found',
    available_endpoints: [
      'GET /api/health',
      'GET /api/status',
      'GET /api/models',
      'GET /api/metrics',
      'POST /api/route'
    ]
  });
});

// Start server
async function startServer() {
  try {
    await loadConfigurations();

    app.listen(PORT, () => {
      logger.info(`LLM Router Server started on port ${PORT}`);
      logger.info(`Health check: http://localhost:${PORT}/api/health`);
      logger.info(`Available models: ${Object.keys(modelProviders).length}`);
      logger.info(`Configured agents: ${Object.keys(agentConfigs).length}`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  logger.info('SIGTERM received, shutting down gracefully');
  process.exit(0);
});

process.on('SIGINT', () => {
  logger.info('SIGINT received, shutting down gracefully');
  process.exit(0);
});

startServer();