locals {
  gh_repos_with_min_approver = { for repo in var.gh_repos : "${repo.repo-id}-${repo.branch-name}" => repo if repo.min-approver >= 1 }
}

resource "github_repository_file" "file_repo" {
  for_each            = local.gh_repos_with_min_approver
  repository          = "${var.prefix}${each.value.repo-id}"
  branch              = each.value.branch-name
  file                = "CODEOWNERS"
  content             = "* @${var.org}/${var.prefix}admins"
  commit_message      = "adding codeowners file"
  overwrite_on_create = true
}

resource "null_resource" "ignore_failure" {
  depends_on = [github_repository_file.file_repo]
  provisioner "local-exec" {
    command = "echo 'Ignoring failure of first resource'"
  }
}

resource "github_repository_ruleset" "ruleset" {
  depends_on = [null_resource.ignore_failure]
  for_each   = { for repo in var.gh_repos : "${repo.repo-id}-${repo.branch-name}" => repo }

  name        = "ruleset-${each.value.repo-id}-${each.value.branch-name}"
  repository  = "${var.prefix}${each.value.repo-id}"
  target      = "branch"
  enforcement = "active"

  conditions {
    ref_name {
      include = [each.value.branch-name]
      exclude = []
    }
  }

  bypass_actors {
    actor_id    = data.github_app.ADO-to-GitHub-Sync.id
    actor_type  = "Integration"
    bypass_mode = "always"
  }

  rules {
    deletion         = true
    non_fast_forward = true

    dynamic "pull_request" {
      for_each = each.value.min-approver > 0 ? [1] : []
      content {
        dismiss_stale_reviews_on_push     = each.value.resetOnSourcePush
        required_approving_review_count   = each.value.min-approver
        require_code_owner_review         = true
        required_review_thread_resolution = each.value.comment-requirement
        require_last_push_approval        = each.value.requireVoteOnLastIteration
      }
    }
  }
}
