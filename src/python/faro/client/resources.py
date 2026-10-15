from pathlib import Path

from faro.shared.textures import load_texture as create_texture


class ResourceManager:
    def __init__(self, resource_root: Path | None = None):
        self.resource_root = (
            resource_root.resolve()
            if resource_root is not None
            else Path(__file__).resolve().parents[3] / "resources"
        )

        self.paths: dict[str, Path] = {}
        self.textures: dict[str, object] = {}

    def resolve(self, resource_id: str, resource_type: str = "") -> Path:
        cache_key = f"{resource_type}:{resource_id}"

        if cache_key in self.paths:
            return self.paths[cache_key]

        namespace, name = resource_id.split(":", 1)

        if namespace != "faro":
            # TODO resource packs support
            raise ValueError(f"Unknown resource namespace: {namespace}")

        # resource_type is a subdirectory of assets, e.g. "textures".
        base = self.resource_root / "assets" / resource_type

        # Prevent absolute paths and ../ traversal outside the resource directory.
        relative_path = Path(name)

        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"Invalid resource path: {resource_id}")

        path = (base / relative_path).resolve()

        if not path.is_relative_to(base.resolve()):
            raise ValueError(f"Resource path escapes resource directory: {resource_id}")

        if not path.is_file():
            raise FileNotFoundError(
                f"Resource '{resource_id}' not found at '{path}'"
            )

        self.paths[cache_key] = path
        return path

    def load_texture(self, resource_id: str):
        if resource_id in self.textures:
            return self.textures[resource_id]

        path = self.resolve(resource_id, "textures")
        texture = create_texture(str(path))

        self.textures[resource_id] = texture
        return self.textures[resource_id]
