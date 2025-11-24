# Configure these variables before running any scripts
export SERVICE_ACCOUNT_ID="cafa-6-pfp-preprocessing-sa"
export SERVICE_ACCOUNT_DISPLAY_NAME="CAFA 6 PFP Preprocessing Service Account"
export PROJECT_ID="cafa-6-pfp"
export REGION="us-west1"
export RESULT_BUCKET_NAME="pfp-data-sagarroytutoring"
export INPUT_BUCKET_NAME="pfp-input-sagarroytutoring"
export BUCKET_PATH="test_1"
export CONTAINER_IMAGE="preprocessing-container"
export INPUT_MOUNT_PATH="/mnt/disks/input"
export RESULT_MOUNT_PATH="/mnt/disks/output"

export MACHINE_TYPE="n2-standard-4"
export PROVISIONING_MODEL="STANDARD"
export MAX_RUN_DURATION="7200s"
export MAX_RETRY_COUNT="2"
export CPU_MILLI="2000"
export MEMORY_MIB="8192"
export COMPLETE_MODE="REMAINING"
export SPAN=""
export TASK_COUNT="1"
export PARALLELISM="1"


# Do not modify below this line
export SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

export TF_VAR_project_id=$PROJECT_ID
export TF_VAR_region=$REGION
export TF_VAR_result_bucket_name=$RESULT_BUCKET_NAME
export TF_VAR_input_bucket_name=$INPUT_BUCKET_NAME
export TF_VAR_service_account_id=$SERVICE_ACCOUNT_ID
export TF_VAR_service_account_display_name=$SERVICE_ACCOUNT_DISPLAY_NAME
