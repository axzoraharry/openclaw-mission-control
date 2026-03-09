#!/usr/bin/env node

import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const TEMPLATES_DIR = path.join(__dirname, '..', 'templates');

const COMMANDS = {
  create,
  'list-templates': listTemplates,
  deploy,
};

function showHelp() {
  console.log(`
SaaS MVP Launcher - Quickly scaffold SaaS applications

Usage:
  saas-mvp-launcher <command> [options]

Commands:
  create <name>           Create a new project
    --template <name>     Template: fullstack, nextjs, fastapi (default: fullstack)
    --auth <provider>     Auth: clerk, local, none (default: local)
    --database <type>     Database: postgres, sqlite, mysql (default: postgres)
    --git                 Initialize git repository
    --install             Install dependencies after creation
  
  list-templates          Show available templates
  
  deploy <path>           Deploy project
    --target <target>     Target: docker, vercel, aws (default: docker)

Examples:
  saas-mvp-launcher create my-saas --template fullstack --auth clerk --git
  saas-mvp-launcher create my-api --template fastapi --database sqlite
  saas-mvp-launcher deploy ./my-saas --target docker
`);
}

function listTemplates() {
  console.log('\nAvailable Templates:\n');
  console.log('  fullstack  - Next.js + FastAPI + PostgreSQL + Docker');
  console.log('  nextjs     - Next.js frontend only');
  console.log('  fastapi    - FastAPI backend only');
  console.log('');
}

function create(projectName, options) {
  if (!projectName) {
    console.error('Error: Project name is required');
    process.exit(1);
  }

  const template = options.template || 'fullstack';
  const auth = options.auth || 'local';
  const database = options.database || 'postgres';
  const projectPath = path.resolve(projectName);

  console.log(`\n🚀 Creating ${template} project: ${projectName}\n`);

  // Check if directory exists
  if (fs.existsSync(projectPath)) {
    console.error(`Error: Directory ${projectName} already exists`);
    process.exit(1);
  }

  // Copy template
  const templatePath = path.join(TEMPLATES_DIR, template);
  if (!fs.existsSync(templatePath)) {
    console.error(`Error: Template '${template}' not found`);
    process.exit(1);
  }

  // Create project directory
  fs.mkdirSync(projectPath, { recursive: true });

  // Copy template files
  copyTemplate(templatePath, projectPath, { projectName, auth, database });

  // Initialize git if requested
  if (options.git) {
    console.log('📦 Initializing git repository...');
    try {
      execSync('git init', { cwd: projectPath, stdio: 'ignore' });
      execSync('git add .', { cwd: projectPath, stdio: 'ignore' });
      execSync('git commit -m "Initial commit"', { cwd: projectPath, stdio: 'ignore' });
      console.log('✅ Git repository initialized\n');
    } catch (e) {
      console.log('⚠️  Git initialization failed (git may not be installed)\n');
    }
  }

  // Install dependencies if requested
  if (options.install) {
    console.log('📦 Installing dependencies...');
    try {
      if (template === 'fullstack' || template === 'nextjs') {
        execSync('npm install', { cwd: projectPath, stdio: 'inherit' });
      }
      if (template === 'fullstack' || template === 'fastapi') {
        const backendPath = template === 'fullstack' ? path.join(projectPath, 'backend') : projectPath;
        if (fs.existsSync(path.join(backendPath, 'requirements.txt'))) {
          execSync('pip install -r requirements.txt', { cwd: backendPath, stdio: 'inherit' });
        }
      }
      console.log('✅ Dependencies installed\n');
    } catch (e) {
      console.log('⚠️  Dependency installation failed\n');
    }
  }

  console.log(`✅ Project created successfully!\n`);
  console.log(`Next steps:`);
  console.log(`  cd ${projectName}`);
  if (template === 'fullstack') {
    console.log(`  docker-compose up -d    # Start database`);
    console.log(`  cd backend && uv run uvicorn app.main:app --reload`);
    console.log(`  cd frontend && npm run dev`);
  } else if (template === 'nextjs') {
    console.log(`  npm run dev`);
  } else if (template === 'fastapi') {
    console.log(`  uv run uvicorn app.main:app --reload`);
  }
  console.log('');
}

function copyTemplate(src, dest, vars) {
  const files = fs.readdirSync(src);

  for (const file of files) {
    const srcPath = path.join(src, file);
    const destPath = path.join(dest, file);
    const stat = fs.statSync(srcPath);

    if (stat.isDirectory()) {
      fs.mkdirSync(destPath, { recursive: true });
      copyTemplate(srcPath, destPath, vars);
    } else {
      let content = fs.readFileSync(srcPath, 'utf-8');
      
      // Replace template variables
      content = content.replace(/{{PROJECT_NAME}}/g, vars.projectName);
      content = content.replace(/{{AUTH_PROVIDER}}/g, vars.auth);
      content = content.replace(/{{DATABASE}}/g, vars.database);
      
      fs.writeFileSync(destPath, content);
    }
  }
}

function deploy(projectPath, options) {
  const target = options.target || 'docker';
  const fullPath = path.resolve(projectPath || '.');

  if (!fs.existsSync(fullPath)) {
    console.error(`Error: Path ${projectPath} does not exist`);
    process.exit(1);
  }

  console.log(`\n🚀 Deploying to ${target}...\n`);

  switch (target) {
    case 'docker':
      deployDocker(fullPath);
      break;
    case 'vercel':
      deployVercel(fullPath);
      break;
    case 'aws':
      console.log('AWS deployment coming soon!');
      break;
    default:
      console.error(`Error: Unknown target '${target}'`);
      process.exit(1);
  }
}

function deployDocker(projectPath) {
  try {
    console.log('Building Docker images...');
    execSync('docker-compose build', { cwd: projectPath, stdio: 'inherit' });
    console.log('\n✅ Docker images built successfully');
    console.log('\nStart with: docker-compose up -d\n');
  } catch (e) {
    console.error('❌ Docker build failed');
    process.exit(1);
  }
}

function deployVercel(projectPath) {
  try {
    console.log('Deploying to Vercel...');
    execSync('npx vercel --yes', { cwd: projectPath, stdio: 'inherit' });
    console.log('\n✅ Deployed to Vercel\n');
  } catch (e) {
    console.error('❌ Vercel deployment failed');
    process.exit(1);
  }
}

// Parse arguments
const args = process.argv.slice(2);
const command = args[0];

if (!command || command === '--help' || command === '-h') {
  showHelp();
  process.exit(0);
}

// Parse options
const options = {};
const positional = [];

for (let i = 1; i < args.length; i++) {
  const arg = args[i];
  if (arg.startsWith('--')) {
    const key = arg.slice(2);
    const nextArg = args[i + 1];
    if (nextArg && !nextArg.startsWith('--')) {
      options[key] = nextArg;
      i++;
    } else {
      options[key] = true;
    }
  } else {
    positional.push(arg);
  }
}

// Execute command
if (COMMANDS[command]) {
  COMMANDS[command](positional[0], options);
} else {
  console.error(`Error: Unknown command '${command}'`);
  showHelp();
  process.exit(1);
}
