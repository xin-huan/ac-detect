"""HuggingFace 鉴权：修补 pyannote 3.1.x 与 huggingface_hub 1.x 的 use_auth_token 不兼容。"""
from typing import Any, Dict
import sys

_logged = False
_patched = False
_hf_hub_download_compat = None


def _make_compat_hf_hub_download():
    from huggingface_hub import hf_hub_download as _original

    def compat(*args, use_auth_token=None, token=None, **kwargs):
        if token is None and use_auth_token is not None:
            token = use_auth_token
        kwargs.pop("use_auth_token", None)
        return _original(*args, token=token, **kwargs)

    return compat


def patch_hf_hub_download() -> None:
    """必须在 import pyannote.audio 之前调用；并修补已加载的 pyannote 子模块。"""
    global _patched, _hf_hub_download_compat
    if _patched:
        return
    _hf_hub_download_compat = _make_compat_hf_hub_download()

    import huggingface_hub
    huggingface_hub.hf_hub_download = _hf_hub_download_compat

    for name, mod in list(sys.modules.items()):
        if mod is None:
            continue
        if hasattr(mod, "hf_hub_download"):
            try:
                setattr(mod, "hf_hub_download", _hf_hub_download_compat)
            except (AttributeError, TypeError):
                pass

    _patched = True


def ensure_hf_login(token: str) -> None:
    global _logged
    patch_hf_hub_download()
    if not token:
        return
    import os
    os.environ["HF_TOKEN"] = token
    os.environ["HUGGING_FACE_HUB_TOKEN"] = token
    if _logged:
        return
    try:
        from huggingface_hub import login
        login(token=token, add_to_git_credential=False)
        _logged = True
    except Exception:
        pass


def _load_pretrained(loader, model_id: str, token: str):
    ensure_hf_login(token)
    # 确保 pyannote 子模块使用兼容函数
    patch_hf_hub_download()
    try:
        import pyannote.audio.core.pipeline as pap
        pap.hf_hub_download = _hf_hub_download_compat
    except ImportError:
        pass
    try:
        import pyannote.audio.core.model as pam
        if hasattr(pam, "hf_hub_download"):
            pam.hf_hub_download = _hf_hub_download_compat
    except ImportError:
        pass

    errors = []
    for kwargs in ({"use_auth_token": token}, {}):
        try:
            return loader.from_pretrained(model_id, **kwargs)
        except Exception as e:
            errors.append(str(e))
    raise RuntimeError(f"加载 {model_id} 失败 — " + " | ".join(errors))


def load_pyannote_pipeline(pipeline_cls, model_id: str, token: str):
    return _load_pretrained(pipeline_cls, model_id, token)


def load_pyannote_model(model_cls, model_id: str, token: str):
    return _load_pretrained(model_cls, model_id, token)


def hf_auth_kwargs(token: str) -> Dict[str, Any]:
    ensure_hf_login(token)
    return {"use_auth_token": token}
