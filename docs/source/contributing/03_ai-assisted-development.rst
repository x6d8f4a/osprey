AI-Assisted Development
========================

Osprey's workflows are designed for AI coding assistants. Use structured prompts to automate testing, documentation, commits, and releases.

----

Getting Started
---------------

Osprey workflows work with AI coding assistants. Choose the tool that fits your workflow:

.. tab-set::

   .. tab-item:: 🎯 Cursor

      **AI-powered code editor** with native ``@`` mentions for workflow files.

      **Platform Support:** Windows, macOS, Linux

      .. dropdown:: Installation Instructions
         :color: info
         :icon: download

         **1. Download:**

         Visit `cursor.com <https://cursor.com>`_ and download for your platform.

         **2. Install:**

         - **Windows:** Run the ``.exe`` installer
         - **macOS:** Open the ``.dmg`` and drag to Applications
         - **Linux:** Install ``.deb`` or ``.rpm`` package for your distribution

         **3. First-Time Setup:**

         - Launch Cursor
         - Complete the setup wizard
         - Create an account to unlock AI features (optional but recommended)
         - Open the Osprey project folder

         .. seealso::
            Official docs: `docs.cursor.com <https://docs.cursor.com/en/get-started/installation>`_

   .. tab-item:: 💬 Claude Code

      **Terminal-based AI assistant** that works alongside your existing editor.

      **Platform Support:** Windows (WSL), macOS, Linux

      .. dropdown:: Installation Instructions
         :color: info
         :icon: download

         **1. Prerequisites:**

         - Node.js 18.0 or higher
         - Internet connection

         **2. Install:**

         .. code-block:: bash

            # Using npm (recommended)
            npm install -g @anthropic-ai/claude-code

            # Or using Homebrew (macOS)
            brew install anthropic/tap/claude-code

         **3. Verify Installation:**

         .. code-block:: bash

            claude --version

         **4. Authenticate:**

         .. code-block:: bash

            claude auth login

         This opens your browser to sign in with your Anthropic account.

         **5. Update:**

         .. code-block:: bash

            # Using npm
            npm update -g @anthropic-ai/claude-code

            # Using Homebrew
            brew upgrade claude-code

         .. seealso::
            Official docs: `docs.anthropic.com <https://docs.anthropic.com/en/docs/claude-code/getting-started>`_

----

Workflow Catalog
----------------

.. tab-set::

   .. tab-item:: 🚀 Quick Workflows
      :sync: quick

      Fast workflows for common tasks (< 5 minutes).

      .. grid:: 2
         :gutter: 3

         .. grid-item-card:: 🔍 Pre-Merge Cleanup
            :link: pre-merge-cleanup
            :link-type: ref

            Scan for common issues before committing.

         .. grid-item-card:: 📝 Docstrings
            :link: docstrings
            :link-type: ref

            Generate proper docstrings for functions and classes.

         .. grid-item-card:: 💬 Comments
            :link: comments
            :link-type: ref

            Add strategic comments to complex code.

   .. tab-item:: 🏗️ Standard Workflows
      :sync: standard

      Comprehensive workflows for development tasks (10-30 minutes).

      .. grid:: 2
         :gutter: 3

         .. grid-item-card:: 🧪 Testing Strategy
            :link: testing
            :link-type: ref

            Cost-aware testing: unit, integration, or e2e?

         .. grid-item-card:: 📦 Commit Organization
            :link: commits
            :link-type: ref

            Organize changes into atomic commits with CHANGELOG entries.

         .. grid-item-card:: 📚 Documentation Updates
            :link: documentation
            :link-type: ref

            Identify and update documentation that needs changes.

         .. grid-item-card:: 🤖 AI Code Review
            :link: ai-review
            :link-type: ref

            Review AI-generated code for quality and correctness.

   .. tab-item:: 🎯 Release Workflows
      :sync: release

      Complete workflows for releases and major changes (1-2 hours).

      .. grid:: 1
         :gutter: 3

         .. grid-item-card:: 🚢 Release Process
            :link: release
            :link-type: ref

            Complete release workflow with testing, versioning, and deployment.

----

Detailed Workflow Guides
------------------------

.. _pre-merge-cleanup:

🔍 Pre-Merge Cleanup
^^^^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/pre-merge-cleanup.md
   :show-use-when:

**Command Line:**

.. code-block:: bash

   ./scripts/premerge_check.sh

**Example:**

.. code-block:: text

   @docs/workflows/pre-merge-cleanup.md Scan my uncommitted changes

**What it checks:**

- Debug code (``print()``, ``breakpoint()``, etc.)
- Missing or incomplete docstrings
- TODO/FIXME comments
- Missing CHANGELOG entries
- Import organization

----

.. _commits:

📦 Commit Organization
^^^^^^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/commit-organization.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/commit-organization.md Help me organize my commits

**Best for:**

- Feature branches with multiple related changes
- Refactoring efforts spanning multiple files
- Bug fixes that touch multiple components
- First-time contributors organizing their PR

.. note::
   Each commit gets its own CHANGELOG entry. Don't batch all entries at the start!

----

.. _testing:

🧪 Testing Strategy
^^^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/testing-workflow.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/testing-workflow.md What type of test should I write?

**Decision Framework:**

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Test Type
     - When to Use
     - Cost/Speed
   * - **Unit**
     - Pure functions, business logic, utilities
     - ⚡ Fast, cheap
   * - **Integration**
     - Component interactions, API endpoints
     - ⚙️ Medium speed/cost
   * - **E2E**
     - Critical user flows, deployment validation
     - 🐌 Slow, expensive

----

.. _documentation:

📚 Documentation Updates
^^^^^^^^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/update-documentation.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/update-documentation.md What docs need updating?

----

.. _docstrings:

📝 Docstrings
^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/docstrings.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/docstrings.md Write a docstring for this function

----

.. _comments:

💬 Comments
^^^^^^^^^^^

.. workflow-summary:: ../../workflows/comments.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/comments.md Add comments to explain this logic

----

.. _ai-review:

🤖 AI Code Review
^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/ai-code-review.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/ai-code-review.md Review this AI-generated code

----

.. _release:

🚢 Release Workflow
^^^^^^^^^^^^^^^^^^^

.. workflow-summary:: ../../workflows/release-workflow.md
   :show-use-when:

**Example:**

.. code-block:: text

   @docs/workflows/release-workflow.md Guide me through releasing v0.9.8

----

Best Practices
--------------

**Do:**

- Reference specific workflows with ``@`` mentions
- Provide context about what you're working on
- Review all AI-generated code carefully
- Run tests to verify AI changes
- Check for security issues in AI code

**Don't:**

- Blindly accept AI suggestions
- Skip testing AI-generated code
- Assume AI knows project-specific details
- Skip pre-merge cleanup checks
- Use AI to write every single line
- Skip human code review

----

Example: Adding a Capability with AI
-------------------------------------

**1. Plan the work:**

.. code-block:: text

   @docs/workflows/ + @docs/source/developer-guides/
   I want to add a capability for archiver data. Help me plan the implementation.

**2. Write the code and docstrings:**

.. code-block:: text

   @docs/workflows/docstrings.md
   Write a docstring for my new capability class

**3. Add appropriate tests:**

.. code-block:: text

   @docs/workflows/testing-workflow.md
   My capability calls an external API. Should I write unit or integration tests?

**4. Update documentation:**

.. code-block:: text

   @docs/workflows/update-documentation.md
   I added a new archiver capability. What documentation needs updating?

**5. Pre-commit cleanup:**

.. code-block:: text

   @docs/workflows/pre-merge-cleanup.md
   Scan my uncommitted changes for issues

**6. Organize commits:**

.. code-block:: text

   @docs/workflows/commit-organization.md
   Help me organize these changes into atomic commits with CHANGELOG entries

----

.. seealso::

   **Explore More:**

   - Browse all workflow files in ``docs/workflows/``
   - :doc:`02_code-standards` for coding conventions
   - :doc:`index` for environment setup
   - :doc:`../developer-guides/index` for technical guides

   **Get Started:**

   Pick a workflow card above and try it with your next change!
