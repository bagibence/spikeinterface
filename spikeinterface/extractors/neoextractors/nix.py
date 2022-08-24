from spikeinterface.core.core_tools import define_function_from_class

from .neobaseextractor import NeoBaseRecordingExtractor, NeoBaseSortingExtractor
from .neo_utils import get_streams, get_num_blocks


class NixRecordingExtractor(NeoBaseRecordingExtractor):
    """
    Class for reading Nix file

    Based on :py:class:`neo.rawio.NIXRawIO`

    Parameters
    ----------
    file_path: str
        The file path to load the recordings from.
    stream_id: str, optional
        If there are several streams, specify the stream id you want to load.
    stream_name: str, optional
        If there are several streams, specify the stream name you want to load.
    block_index: int, optional
        If there are several blocks, specify the block index you want to load.
    all_annotations: bool, optional, default: False
        Load exhaustively all annotations from neo.
    """
    mode = 'file'
    NeoRawIOClass = 'NIXRawIO'

    def __init__(self, file_path, stream_id=None, stream_name=None, block_index=None, all_annotations=False):
        neo_kwargs = {'filename': str(file_path)}
        NeoBaseRecordingExtractor.__init__(self, stream_id=stream_id, 
                                           stream_name=stream_name,
                                           block_index=block_index,
                                           all_annotations=all_annotations, 
                                           **neo_kwargs)
        self._kwargs.update(dict(file_path=str(file_path), stream_id=stream_id))
        self.extra_requirements.append('nixio')


read_nix = define_function_from_class(source_class=NixRecordingExtractor, name="read_nix")


def get_nix_streams(file_path):
    """Return available NEO streams

    Parameters
    ----------
    file_path : str
        The file path to load the recordings from.

    Returns
    -------
    list
        List of stream names
    list
        List of stream IDs
    """
    raw_class = NixRecordingExtractor.NeoRawIOClass
    neo_kwargs = {'filename': str(file_path)}
    return get_streams(raw_class, **neo_kwargs)


def get_nix_num_blocks(file_path):
    """Return number of NEO blocks

    Parameters
    ----------
    file_path : str
        The file path to load the recordings from.

    Returns
    -------
    int
        Number of NEO blocks
    """
    raw_class = NixRecordingExtractor.NeoRawIOClass
    neo_kwargs = {'filename': str(file_path)}
    return get_num_blocks(raw_class, **neo_kwargs)
