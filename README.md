python3 -m pip install openai langchain streamlit pandas

mkdir .streamlit
touch .streamlit/secrets.toml
openai_api_key = "sk-your-actual-api-key-here"

For Production/Streamlit Cloud:
Go to your app dashboard on Streamlit Cloud
Navigate to App Settings > Secrets
Add your secret in the same format:
```
openai_api_key = "sk-your-actual-api-key-here"
```
You can then access the secret in your code using:
```
openai_api_key = st.secrets["openai_api_key"]
```

### Sure but how do we deploy the app?

- Test in Streamlit Cloud (but this doesn't allow custom domain names)
- Build, containerize, and deploy to Docker Hub
- Test the Docker runs locally
- Deploy docker to Google Cloud Run
- Test the docker runs on Google Cloud Run
- Set up a custom domain name

Pick the right project
```
gcloud config set project <project-id>
```

Get service account id.
- Go to IAM & Admin > Service Accounts


# Step 1: Create a Docker Container from Your Local Project

## 1. Navigate to Your Project Directory
Ensure you are in the root directory of your project where the `Dockerfile` is located. For example:
```bash
cd /docs_agent
```

## 2. Build the Docker Image
Use the following command to build your Docker container locally. Replace `[IMAGE_NAME]` with the desired name for your Docker image:
```bash
docker build -t ottobot-prod:latest .
```
This command creates a Docker image tagged as `latest` based on the instructions in your `Dockerfile`.

## 3. Test the Docker Image Locally (Optional)
Run the Docker container locally to ensure it works as expected:
```bash
docker run -p 8080:8080 ottobot-prod:latest
```
Replace `8080:8080` with the port mapping appropriate for your application.

---

# Step 2: Grant IAM Policy Bindings for GCP Services

## 1. Grant Storage Access
Grant the Compute Engine service account the `roles/storage.objectUser` role to interact with storage objects:
```bash
gcloud projects add-iam-policy-binding natural-quasar-473511-v6 \
    --member=serviceAccount:$(gcloud projects describe natural-quasar-473511-v6 \
    --format="value(projectNumber)")-compute@developer.gserviceaccount.com \
    --role="roles/storage.objectUser"
```

## 2. Grant Write Access to Artifact Registry
Grant the Compute Engine service account the `roles/artifactregistry.writer` role to push Docker images:
```bash
gcloud projects add-iam-policy-binding natural-quasar-473511-v6 \
    --member=serviceAccount:$(gcloud projects describe natural-quasar-473511-v6 \
    --format="value(projectNumber)")-compute@developer.gserviceaccount.com \
    --role="roles/artifactregistry.writer"
```

## 3. Grant Cloud Run Admin Permissions
Grant the Compute Engine service account the `roles/run.admin` role to manage Cloud Run services:
```bash
gcloud projects add-iam-policy-binding natural-quasar-473511-v6 \
    --member=serviceAccount:$(gcloud projects describe natural-quasar-473511-v6 \
    --format="value(projectNumber)")-compute@developer.gserviceaccount.com \
    --role="roles/run.admin"
```

---

# Step 3: Create and Configure an Artifact Registry

## 1. Create a Docker Repository
Create an Artifact Registry repository to store your Docker image. Replace  with your preferred region:
```bash
gcloud artifacts repositories create ottobot-docker-repo-prod \
    --repository-format=docker --location=asia-east1 \
    --description="Ottobot full service docker repository in asia for production"
```

## 2. Verify the Repository
Confirm that the repository was created successfully:
```bash
gcloud artifacts repositories list
```

---

# Step 4: Build and Push the Docker Image to Artifact Registry

## 1. Build and Push the Image
Use the following command to build and push your Docker image to Artifact Registry. Replace `[PROJECT_ID]` with your GCP project ID:
```bash
gcloud builds submit --region=asia-east1 \
    --tag asia-east1-docker.pkg.dev/natural-quasar-473511-v6/ottobot-docker-repo-prod/ottobot-prod:latest
```

---

# Step 5: Deploy the Docker Image to Cloud Run
****
## 1. Deploy the Image
Deploy the Docker image from Artifact Registry to Cloud Run. Replace `[PROJECT_ID]` with your GCP project ID:
```bash
gcloud run deploy ottobot-service-prod \
    --image asia-east1-docker.pkg.dev/natural-quasar-473511-v6/ottobot-docker-repo-prod/ottobot-prod:latest \
    --region asia-east1 \
    --platform managed \
    --allow-unauthenticated
```

## 2. Access Your Service
After deployment, Cloud Run will provide a public URL for your service. Open the URL in your browser to verify your app is running.

---

# Optional: Validation Commands

## Validate IAM Policies
Verify the roles assigned to the Compute Engine service account:
```bash
gcloud projects get-iam-policy natural-quasar-473511-v6 \
    --flatten="bindings[].members" \
    --filter="bindings.members:$(gcloud projects describe natural-quasar-473511-v6 --format="value(projectNumber)")-compute@developer.gserviceaccount.com" \
    --format="table(bindings.role)"
```

## Cleanup Resources
If you no longer need the resources, delete the Cloud Run service and Artifact Registry repository:
```bash
gcloud run services delete ottobot-service --region=asia-east1

gcloud artifacts repositories delete ottobot-docker-repo-prod --location=asia-east1
```

### Failed Permissions Initially
```
ERROR: (gcloud.projects.add-iam-policy-binding) User [adrianoligarch@gmail.com] does not have permission to access projects instance [constant-blend-398005:setIamPolicy] (or it may not exist): Policy update access denied.

ERROR: (gcloud.builds.submit) FAILED_PRECONDITION: invalid bucket "489071396932.cloudbuild-logs.googleusercontent.com"; service account 489071396932-compute@developer.gserviceaccount.com does not have access to the bucket

  Setting IAM policy failed, try "gcloud beta run services add-iam-policy-binding --region=australia-southeast1 --member=allUsers --role=roles/run.invoker ottobot-service"
```
