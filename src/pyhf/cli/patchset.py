"""The pyhf spec CLI subcommand."""
import logging

import click
import json
import sys

from ..patchset import PatchSet
from ..workspace import Workspace
from .. import utils

logging.basicConfig()
log = logging.getLogger(__name__)


@click.group(name='patchset')
def cli():
    """Operations involving patchsets."""


@cli.command()
@click.argument('patchset', default='-')
@click.option(
    '--name', help='The name of the patch to extract.', default=None,
)
@click.option(
    '--output-file',
    help='The location of the output json file. If not specified, prints to screen.',
    default=None,
)
@click.option(
    '--with-metadata/--without-metadata',
    default=False,
    help="Include patchset metadata in output.",
)
def extract(patchset, name, output_file, with_metadata):
    """
    Extract a patch from a patchset.

    If the patchset does not contain the name, will exit with code 1.

    Returns:
        jsonpatch (:obj:`list`): A list of jsonpatch operations to apply to a workspace.
    """
    with click.open_file(patchset, 'r') as fstream:
        patchset_spec = json.load(fstream)

    patchset = PatchSet(patchset_spec)
    patch = patchset[name]

    if with_metadata:
        result = {'metadata': patch.metadata, 'patch': patch.patch}
        result['metadata'].update(patchset.metadata)
    else:
        result = patch.patch

    if output_file:
        with open(output_file, 'w+') as out_file:
            json.dump(result, out_file, indent=4, sort_keys=True)
        log.debug("Written to {0:s}".format(output_file))
    else:
        click.echo(json.dumps(result, indent=4, sort_keys=True))


@cli.command()
@click.argument('background-only', default='-')
@click.argument('patchset', default='-')
@click.option(
    '--name', help='The name of the patch to extract.', default=None,
)
@click.option(
    '--output-file',
    help='The location of the output json file. If not specified, prints to screen.',
    default=None,
)
def apply(background_only, patchset, name, output_file):
    """
    Apply a patch from patchset to the background-only workspace.

    If the patchset does not contain the name, will exit with code 1.
    If the patchset is not associated with the background-only workspace, will exit with code 2.

    Returns:
        workspace (~pyhf.workspace.Workspace): The patched background-only workspace.
    """
    with click.open_file(background_only, 'r') as specstream:
        spec = json.load(specstream)

    utils.validate(spec, 'workspace.json')

    with click.open_file(patchset, 'r') as fstream:
        patchset_spec = json.load(fstream)

    patchset = PatchSet(patchset_spec)

    for hash_alg, digest in patchset.digests.items():
        digest_calc = utils.digest(spec, algorithm=hash_alg)
        if not digest_calc == digest:
            click.echo(
                f"The digest verification failed for hash algorithm '{hash_alg}'.\n\tExpected: {digest}.\n\tGot:     {digest_calc}"
            )
            sys.exit(2)

    patch = patchset[name]
    patched_spec = patch.apply(spec)

    patched_ws = Workspace(patched_spec)

    if output_file:
        with open(output_file, 'w+') as out_file:
            json.dump(patched_ws, out_file, indent=4, sort_keys=True)
        log.debug("Written to {0:s}".format(output_file))
    else:
        click.echo(json.dumps(patched_ws, indent=4, sort_keys=True))


@cli.command()
@click.argument('background-only', default='-')
@click.argument('patchset', default='-')
def verify(background_only, patchset):
    """
    Verify the patchset digest against the background-only workspace.

    If the patchset is not associated with the background-only workspace, will exit with code 2.

    Returns:
        workspace (~pyhf.workspace.Workspace): The patched background-only workspace.
    """
    with click.open_file(background_only, 'r') as specstream:
        spec = json.load(specstream)

    utils.validate(spec, 'workspace.json')

    with click.open_file(patchset, 'r') as fstream:
        patchset_spec = json.load(fstream)

    patchset = PatchSet(patchset_spec)

    for hash_alg, digest in patchset.digests.items():
        digest_calc = utils.digest(spec, algorithm=hash_alg)
        if not digest_calc == digest:
            click.echo(
                f"The digest verification failed for hash algorithm '{hash_alg}'.\n\tExpected: {digest}.\n\tGot:     {digest_calc}"
            )
            sys.exit(2)
    click.echo("All good.")
