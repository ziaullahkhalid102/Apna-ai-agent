"""DOM parsing and element extraction for browser automation."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class DOMElement:
    tag: str
    text: str = ""
    attributes: dict[str, str] = field(default_factory=dict)
    children: list[DOMElement] = field(default_factory=list)
    selector: str = ""
    is_interactive: bool = False
    bounding_box: dict[str, float] | None = None

    @property
    def summary(self) -> str:
        parts = [f"<{self.tag}"]
        for key in ("id", "class", "role", "aria-label", "name", "type", "href", "placeholder"):
            if key in self.attributes:
                parts.append(f' {key}="{self.attributes[key]}"')
        parts.append(">")
        if self.text:
            parts.append(self.text[:100])
        return "".join(parts)


INTERACTIVE_TAGS = {"a", "button", "input", "select", "textarea", "details", "summary"}
INTERACTIVE_ROLES = {
    "button",
    "link",
    "textbox",
    "checkbox",
    "radio",
    "combobox",
    "listbox",
    "menuitem",
    "tab",
    "switch",
}


class DOMParser:
    """Parses raw HTML/accessibility tree into structured interactive elements."""

    def parse_accessibility_tree(self, tree_data: list[dict]) -> list[DOMElement]:
        elements: list[DOMElement] = []
        for node in tree_data:
            element = self._parse_ax_node(node)
            if element:
                elements.append(element)
        return elements

    def _parse_ax_node(self, node: dict) -> DOMElement | None:
        role = node.get("role", "")
        name = node.get("name", "")

        if not role or role in ("none", "generic", "group"):
            return None

        is_interactive = role.lower() in INTERACTIVE_ROLES
        attrs: dict[str, str] = {"role": role}
        if name:
            attrs["aria-label"] = name

        for prop in node.get("properties", []):
            attrs[prop["name"]] = str(prop.get("value", {}).get("value", ""))

        return DOMElement(
            tag=role,
            text=name,
            attributes=attrs,
            is_interactive=is_interactive,
        )

    def extract_interactive_elements(self, elements: list[DOMElement]) -> list[DOMElement]:
        return [el for el in elements if el.is_interactive]

    def build_dom_summary(self, elements: list[DOMElement], max_elements: int = 100) -> str:
        interactive = self.extract_interactive_elements(elements)
        lines: list[str] = [f"Page has {len(elements)} elements, {len(interactive)} interactive:\n"]

        for i, el in enumerate(interactive[:max_elements]):
            bbox_str = ""
            if el.bounding_box:
                bbox_str = (
                    f" @({el.bounding_box.get('x', 0):.0f},{el.bounding_box.get('y', 0):.0f})"
                )
            lines.append(f"[{i}] {el.summary}{bbox_str}")

        if len(interactive) > max_elements:
            lines.append(f"\n... and {len(interactive) - max_elements} more interactive elements")

        return "\n".join(lines)

    def find_element_by_text(self, elements: list[DOMElement], text: str) -> DOMElement | None:
        text_lower = text.lower()
        for el in elements:
            if text_lower in el.text.lower():
                return el
            label = el.attributes.get("aria-label", "")
            if text_lower in label.lower():
                return el
        return None

    def find_elements_by_role(self, elements: list[DOMElement], role: str) -> list[DOMElement]:
        return [el for el in elements if el.attributes.get("role", "").lower() == role.lower()]
