data "github_app" "ADO-to-GitHub-Sync" {
  slug = "ADO-to-GitHub-Sync"
}

variable "gh_repos" {
  type = list(object({
    repo-id                     = string
    branch-name                 = string
    min-approver                = number
    merge-strategy              = list(string)
    comment-requirement         = bool
    creatorVoteCounts           = bool
    allowDownvotes              = bool
    resetOnSourcePush           = bool
    requireVoteOnLastIteration  = bool
    resetRejectionsOnSourcePush = bool
    blockLastPusherVote         = bool
    requireVoteOnEachIteration  = bool
  }))
}

variable "prefix" {
  type    = string
  default = "__prefix__"
}

variable "org" {
  type    = string
  default = "Deloitte-US-Consulting-HO"
}