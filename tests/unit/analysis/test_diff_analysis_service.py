"""Unit tests for DiffAnalysisService."""

import pytest

from code_impact.infrastructure.analysis.diff_analysis_service import DiffAnalysisService

DIFF = """\
diff --git a/app/service.py b/app/service.py
--- a/app/service.py
+++ b/app/service.py
@@ -1,4 +1,7 @@
 import os
 
 def run():
     return True
+
+def shutdown():
+    return False
"""

BEFORE = "import os\n\ndef run():\n    return True\n"
AFTER = "import os\n\ndef run():\n    return True\n\ndef shutdown():\n    return False\n"


@pytest.mark.asyncio
async def test_enriched_analysis():
    service = DiffAnalysisService()
    result = await service.analyze(
        DIFF,
        file_contents_before={"app/service.py": BEFORE},
        file_contents_after={"app/service.py": AFTER},
    )

    assert "app/service.py" in result.changed_files
    assert result.complexity_delta >= 0
    assert len(result.file_changes) == 1
    assert "shutdown" in result.file_changes[0].functions_added
