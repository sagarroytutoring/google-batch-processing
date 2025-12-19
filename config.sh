# Configure these variables before running any scripts
export SERVICE_ACCOUNT_ID="cafa-6-pfp-preprocessing-sa"  # Not implemented
export SERVICE_ACCOUNT_DISPLAY_NAME="CAFA 6 PFP Preprocessing Service Account"
export PROJECT_ID="cafa-6-pfp"
export REGION="us-west1"
export OUTPUT_BUCKET_NAME="pfp-data-sagarroytutoring"
export INPUT_BUCKET_NAME="pfp-input-sagarroytutoring"
export CONTAINER_IMAGE="preprocessing-container"

# Job configuration
export MACHINE_TYPE="n2-highmem-4"
export CPU_MILLI="1000"
export MEMORY_MIB="8192"  # Correct amount of resources for 4 tasks on n2-highmem-4
export GPU_TYPE=""  # If specified, the machine type is ignored (Not implemented yet)
export GPU_COUNT=""
export PROVISIONING_MODEL="SPOT"
export MAX_RUN_DURATION="86400s"
export MAX_RETRY_COUNT="5"
export COMPLETE_MODE="REMAINING"
export SPAN=""  # Only use if input files are numbered!
export TASK_COUNT="28"
export PARALLELISM="28"  # vCPU quota is currently 48
export INPUT_BUCKET_PATH="train_sequences.fasta"
export INPUT_PACKED="true"
export OUTPUT_BUCKET_PATH="esm_cafa6_t33_3"
export OUTPUT_ZIPPED="true"
export COMPUTE_LOCATION="regions/us-west1"

export HF_MODEL_DOWNLOADS="facebook/esm2_t33_650M_UR50D"


# Do not modify below this line
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"
export INPUT_MOUNT_PATH="/mnt/disks/input"
export OUTPUT_MOUNT_PATH="/mnt/disks/output"
export CHECKPOINT_INTERVAL="30"
export OUTPUT_BUCKET_LS_NAME="output_bucket_files.txt"

export TF_VAR_project_id=$PROJECT_ID
export TF_VAR_region=$REGION
export TF_VAR_result_bucket_name=$OUTPUT_BUCKET_NAME
export TF_VAR_input_bucket_name=$INPUT_BUCKET_NAME
export TF_VAR_service_account_id=$SERVICE_ACCOUNT_ID
export TF_VAR_service_account_display_name=$SERVICE_ACCOUNT_DISPLAY_NAME
