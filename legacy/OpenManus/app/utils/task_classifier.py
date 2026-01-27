"""LLM-based task classification for intelligent workspace organization"""

from typing import List, Optional, Tuple, Dict
from app.llm import LLM
from app.schema import Message
from app.logger import logger


class TaskClassifier:
    """Intelligent task classifier using LLM for semantic understanding"""

    CLASSIFICATION_PROMPT = """
    Analyze the user's request and classify it into one of these categories:
    - data_analysis: Data processing, visualization, statistical analysis, ML tasks
    - code_generation: Writing code, implementing features, creating functions/classes
    - documentation: Creating reports, documentation, technical writing
    - web_scraping: Web data extraction, browser automation, API integration
    - system_ops: File operations, system configuration, DevOps tasks
    - research: Information gathering, comparison, investigation
    - general: Tasks that don't fit other categories

    User request: {prompt}

    Respond with ONLY the category name and a confidence score (0-1).
    Format: category_name|confidence_score
    Example: data_analysis|0.95
    """

    TAG_GENERATION_PROMPT = """
    Generate 3-5 relevant tags for this {category} task:
    "{prompt}"

    Return only comma-separated tags, no explanations.
    """

    def __init__(self, llm: Optional[LLM] = None):
        """
        Initialize classifier with LLM instance

        Args:
            llm: LLM instance to use for classification
        """
        self.llm = llm or LLM(config_name="default")
        self.cache: Dict[str, Tuple[str, float, List[str]]] = {}
        logger.debug("TaskClassifier initialized")

    async def classify_task(self, prompt: str) -> Tuple[str, float, List[str]]:
        """
        Classify task using LLM understanding

        Args:
            prompt: User's task description

        Returns:
            Tuple of (category, confidence, suggested_tags)
        """
        # Check cache first
        cache_key = prompt[:200]  # Use first 200 chars as cache key
        if cache_key in self.cache:
            logger.debug(f"Using cached classification for prompt")
            return self.cache[cache_key]

        try:
            # Prepare classification prompt
            classification_prompt = self.CLASSIFICATION_PROMPT.format(
                prompt=prompt[:500]  # Limit prompt length to avoid token issues
            )

            # Call LLM for classification
            messages = [Message.system_message(classification_prompt)]
            response = await self.llm.ask(
                messages=messages,
                temperature=0.3,  # Lower temperature for consistent classification
                max_tokens=50
            )

            # Parse response
            result = response.content.strip()
            category, confidence = self._parse_classification_response(result)

            # Generate tags
            tags = await self.generate_tags(prompt, category)

            # Cache result
            classification_result = (category, confidence, tags)
            self.cache[cache_key] = classification_result

            logger.info(f"Task classified as '{category}' with confidence {confidence:.2f}")
            return classification_result

        except Exception as e:
            logger.error(f"LLM classification failed: {e}, using fallback")
            return self.fallback_classification(prompt)

    async def generate_tags(self, prompt: str, category: str) -> List[str]:
        """
        Generate relevant tags for the task

        Args:
            prompt: Original user prompt
            category: Classified category

        Returns:
            List of relevant tags
        """
        try:
            tag_prompt = self.TAG_GENERATION_PROMPT.format(
                category=category,
                prompt=prompt[:200]
            )

            messages = [Message.system_message(tag_prompt)]
            response = await self.llm.ask(
                messages=messages,
                temperature=0.5,
                max_tokens=50
            )

            # Parse tags from response
            tags_text = response.content.strip()
            tags = [tag.strip() for tag in tags_text.split(",") if tag.strip()]

            # Ensure we have at least the category as a tag
            if not tags:
                tags = [category]

            # Limit to 5 tags
            return tags[:5]

        except Exception as e:
            logger.warning(f"Tag generation failed: {e}")
            return [category]  # Fallback to category as tag

    def _parse_classification_response(self, response: str) -> Tuple[str, float]:
        """
        Parse LLM classification response

        Args:
            response: LLM response string

        Returns:
            Tuple of (category, confidence)
        """
        try:
            if "|" in response:
                parts = response.split("|")
                category = parts[0].strip().lower()
                confidence = float(parts[1].strip())
            else:
                # If format is incorrect, try to extract category
                category = response.strip().lower()
                confidence = 0.5  # Low confidence for uncertain parsing

            # Validate category
            valid_categories = [
                "data_analysis", "code_generation", "documentation",
                "web_scraping", "system_ops", "research", "general"
            ]

            if category not in valid_categories:
                logger.warning(f"Invalid category '{category}', defaulting to 'general'")
                category = "general"
                confidence = 0.3

            return category, max(0.0, min(1.0, confidence))  # Clamp confidence to [0, 1]

        except Exception as e:
            logger.error(f"Failed to parse classification response: {e}")
            return "general", 0.3

    def fallback_classification(self, prompt: str) -> Tuple[str, float, List[str]]:
        """
        Rule-based fallback classification

        Args:
            prompt: User prompt to classify

        Returns:
            Tuple of (category, confidence, tags)
        """
        prompt_lower = prompt.lower()

        # Keywords for each category (multilingual support)
        rules = [
            ("data_analysis", ["分析", "統計", "圖表", "數據", "視覺化", "data", "plot", "chart", "analyze", "statistics"]),
            ("code_generation", ["寫", "程式", "開發", "實作", "代碼", "code", "function", "implement", "develop", "class"]),
            ("documentation", ["文檔", "文件", "報告", "說明", "document", "report", "readme", "guide", "manual"]),
            ("web_scraping", ["爬", "抓取", "網頁", "瀏覽器", "scrape", "crawl", "web", "browser", "selenium"]),
            ("system_ops", ["檔案", "系統", "配置", "部署", "file", "system", "config", "deploy", "docker"]),
            ("research", ["研究", "調查", "比較", "查找", "research", "investigate", "compare", "search", "find"])
        ]

        for category, keywords in rules:
            matching_keywords = [kw for kw in keywords if kw in prompt_lower]
            if matching_keywords:
                # Confidence based on number of matching keywords
                confidence = min(0.4 + len(matching_keywords) * 0.1, 0.7)
                tags = list(set([category] + matching_keywords[:3]))  # Use matched keywords as tags
                logger.debug(f"Fallback classified as '{category}' with keywords: {matching_keywords}")
                return category, confidence, tags

        # Default to general with low confidence
        return "general", 0.4, ["general"]

    def get_category_description(self, category: str) -> str:
        """
        Get human-readable description of a category

        Args:
            category: Category name

        Returns:
            Description string
        """
        descriptions = {
            "data_analysis": "Data Analysis & Visualization",
            "code_generation": "Code Generation & Development",
            "documentation": "Documentation & Reports",
            "web_scraping": "Web Scraping & Automation",
            "system_ops": "System Operations & Configuration",
            "research": "Research & Investigation",
            "general": "General Tasks"
        }
        return descriptions.get(category, "Unknown Category")