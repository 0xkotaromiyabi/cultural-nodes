#!/bin/bash

# Display ASCII Banner
cat << 'EOF'
   ___      _ _                  _   _   _         _       
  / __\_  _| | |_ _   _ _ __ __ _| | | \ | | ___  | |_ ___ 
 / /  | | | | | __| | | | '__/ _` | | |  \| |/ _ \ | __/ __|
/ /___| |_| | | |_| |_| | | | (_| | | | |\  | (_) || |_\__ \
\____/ \__,_|_|\__|\__,_|_|  \__,_|_| |_| \_|\___/  \__|___/
                                                             
          Cultural AI - Knowledge Assistant

EOF

# Run Ollama model
ollama run cultural-nodes-llama "$@"
