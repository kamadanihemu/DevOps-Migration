#iterate through the all the repos in the organization
terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 6.0"
    }
  }
}

# Configure the GitHub Provider
provider "github" {
  owner = "__ghorg__"
  token = "__GH_PAT__"
}

// terraform {
//   backend "azurerm" {
//     resource_group_name  = "AZRG-DEP-DEL-AUTMN-ISOSBX"
//     storage_account_name = "adoterraformbackend"
//     container_name       = "statefilecontainer"
//     key                  = "terraform.tfstate"
//     access_key           = "__access_key__"
//   }
// }