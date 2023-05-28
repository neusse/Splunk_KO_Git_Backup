# Check if the current directory is a Git repository
if (!(Test-Path -Path ".git" -PathType Container)) {
    # If it is not a Git repository, initialize a new one
    git init
}

# Stage any new files in subdirectories
git add .

# Commit the changes
git commit -m "Added new files in subdirectories"
