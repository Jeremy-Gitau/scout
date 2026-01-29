#!/bin/bash
# Quick script to push to GitHub and trigger multi-platform builds

echo "🚀 Scout - Push to GitHub"
echo "========================="
echo ""

# Check if remote exists
if ! git remote get-url origin &> /dev/null; then
    echo "❌ No remote repository configured!"
    echo ""
    echo "To add your GitHub repository:"
    echo "1. Create a new repository on GitHub (https://github.com/new)"
    echo "2. Run this command (replace with your repo URL):"
    echo "   git remote add origin https://github.com/yourusername/scout.git"
    echo ""
    exit 1
fi

# Show current status
echo "📊 Current status:"
git status --short

echo ""
echo "📍 Remote:"
git remote get-url origin

echo ""
read -p "Push to GitHub? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🔄 Pushing to GitHub..."
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Successfully pushed!"
        echo ""
        echo "🏗️  GitHub Actions will now build Scout for:"
        echo "   • Windows (Scout.exe)"
        echo "   • macOS (Scout)"
        echo "   • Linux (Scout)"
        echo ""
        echo "📦 To create a release:"
        echo "   1. Go to your GitHub repository"
        echo "   2. Click 'Actions' to see build progress"
        echo "   3. Or create a tag for auto-release:"
        echo "      git tag v1.0.0"
        echo "      git push origin v1.0.0"
        echo ""
        echo "🌐 View builds at: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]\(.*\)\.git/\1/')/actions"
    else
        echo ""
        echo "❌ Push failed. Check your credentials and try again."
    fi
else
    echo ""
    echo "❌ Push cancelled."
fi
