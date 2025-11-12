#!/usr/bin/env bash
set -o errexit  # Exit on first error

echo "🔧 Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

echo "📦 Installing requirements..."
pip install -r requirements.txt

echo "✅ Build complete!"
