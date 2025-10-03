from .schemas import TranscriptMessage


def convert_transcript_message_to_xml(message: TranscriptMessage, index: int = None) -> str:
    xml_parts = ["<message>"]
    
    if index is not None:
        xml_parts.append(f"  <index>{index}</index>")
    
    xml_parts.append(f"<id>{message.id}</id>")
    xml_parts.append(f"<role>{message.role}</role>")
    xml_parts.append(f"<content>{message.content}</content>")
    xml_parts.append("</message>")
    
    return "".join(xml_parts)
