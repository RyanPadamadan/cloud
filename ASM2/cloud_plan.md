Great — starting from a clean slate makes this structured and easy to control.

---

## ✅ STEP 1: Set Up EC2, Load Balancer, and Auto Scaling Group

We’ll break Step 1 into small manageable actions.

---

### 🔹 **Step 1.1 – Create a Key Pair**

**Purpose**: So you can SSH into EC2 instances.

1. Go to **EC2 Console → Key Pairs**
2. Click **Create key pair**

   * Name: `ec2-keypair`
   * Type: RSA
   * File format: `.pem`
3. Save the file securely — you’ll use it to SSH.

---

### 🔹 **Step 1.2 – Create a VPC and Networking**

Instead of using default VPC, create a new VPC for clarity and isolation.

#### 📦 VPC Setup:

1. **VPC Console → Create VPC**

   * Name: `image-app-vpc`
   * IPv4 CIDR block: `10.0.0.0/16`
   * Tenancy: Default

2. **Create Two Subnets**

   * One **public** (for ALB and Bastion)

     * CIDR: `10.0.1.0/24`
   * One **private** (for EC2 instances)

     * CIDR: `10.0.2.0/24`

3. **Create an Internet Gateway**

   * Attach it to `image-app-vpc`

4. **Create a Route Table**

   * Associate it with the public subnet
   * Add route: `0.0.0.0/0 → Internet Gateway`

---

### 🔹 **Step 1.3 – Create a Security Group**

Create **two SGs**:

#### `bastion-sg`

* Inbound: SSH (22) from **your IP**
* Outbound: All traffic (default)

#### `webapp-sg`

* Inbound:

  * HTTP (80) from **ALB**
  * SSH (22) from **bastion-sg**
* Outbound: All traffic (default)

---

### 🔹 **Step 1.4 – Launch a Bastion Host**

(You can skip if not using a private subnet for EC2)

1. Launch EC2 Instance:

   * Name: `bastion-host`
   * AMI: Amazon Linux 2
   * Subnet: Public subnet
   * SG: `bastion-sg`
   * Key pair: `ec2-keypair`

---

### 🔹 **Step 1.5 – Create a Launch Template for the App**

**EC2 → Launch Templates → Create Template**

* Name: `image-app-template`
* AMI: Amazon Linux 2 or Ubuntu
* Instance type: `t2.micro` (free tier or cost-effective)
* Key pair: `ec2-keypair`
* Security Group: `webapp-sg`
* Subnet: Private subnet (optional, ALB will route)
* User Data (example below)

---

### 🧾 Sample EC2 User Data Script

```bash
#!/bin/bash
yum update -y
yum install python3 git -y
pip3 install flask pymysql boto3

# Download your app files (manually replace if needed)
cd /home/ec2-user
git clone https://github.com/yourusername/image-caption-app.git
cd image-caption-app

# Set ENV variables (replace with real values)
echo 'export FLASK_APP=app.py' >> ~/.bashrc
echo 'export DB_HOST="your-rds-endpoint"' >> ~/.bashrc
echo 'export DB_USER="admin"' >> ~/.bashrc
echo 'export DB_PASSWORD="yourpassword"' >> ~/.bashrc
echo 'export S3_BUCKET="your-bucket-name"' >> ~/.bashrc
source ~/.bashrc

# Run the app (or replace with gunicorn + nginx)
flask run --host=0.0.0.0 --port=80
```

---

### 🔹 **Step 1.6 – Create Application Load Balancer (ALB)**

**EC2 → Load Balancers → Create Application Load Balancer**

* Name: `image-app-alb`
* Scheme: Internet-facing
* Listeners: HTTP (80)
* Availability Zones: public subnet

**Create Target Group**

* Type: Instance
* Protocol: HTTP
* Health check: `/gallery` or `/`

**Register targets later via ASG**

---

### 🔹 **Step 1.7 – Create Auto Scaling Group (ASG)**

**EC2 → Auto Scaling Groups → Create ASG**

* Launch Template: `image-app-template`
* VPC: `image-app-vpc`
* Subnet: private subnet
* Attach to Target Group (created above)
* Desired capacity: 1, Min: 1, Max: 3
* Scaling policies:

  * Target tracking → Average CPU: 50%
* Enable health checks from ALB

---

### ✅ At the end of Step 1:

You’ll have:

* A **working ALB** pointing to an EC2 app instance
* A **Launch Template** used by the ASG
* **Bastion access** if using private subnets
* Your web app running on a scalable EC2 setup

---

Would you like help:

* Writing a `cloud-init` version of the user data?
* Building a GitHub repo to clone into EC2?
* Or just ready to **create the RDS instance next**?
