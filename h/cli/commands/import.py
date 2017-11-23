# -*- coding: utf-8 -*-

from os import getenv
import json

import click
import requests

from h.schemas.annotation_import import AnnotationImportSchema


def err_echo(message):
    click.echo(message, err=True)


def required_envvar(envvar):
    result = getenv(envvar)
    if not result:
        raise click.ClickException('The {} environment variable is required'.format(envvar))
    return result


@click.command('import')
@click.argument('annotation_file', type=click.File('rb'))
def import_annotations(annotation_file):

    token = required_envvar('H_API_TOKEN')
    api_root = required_envvar('H_API_ROOT')
    group_id = required_envvar('H_GROUP')

    auth_headers = {'Authorization': 'Bearer {}'.format(token)}

    api_index = requests.get(api_root).json()

    profile_url = api_index['links']['profile']['read']['url']

    profile = requests.get(profile_url, headers=auth_headers).json()

    err_echo('Importing as {}'.format(profile['userid']))
    with annotation_file:
        raw_annotations = json.load(annotation_file)

    err_echo('{} annotations to import'.format(len(raw_annotations)))

    schema = AnnotationImportSchema()
    validated_annotations = [schema.validate(ann) for ann in raw_annotations]

    top_level = [a for a in validated_annotations if a['motivation'] == 'commenting']
    replies = [a for a in validated_annotations if a['motivation'] == 'replying']
    err_echo('{} top-level annotations'.format(len(top_level)))
    err_echo('{} replies'.format(len(replies)))

    shared_permissions = {
            'read': ['group:{}'.format(group_id)],
    }

    def top_level_payload(annotation):
        return {
                'group': group_id,
                'permissions': shared_permissions,
                'references': [],
                'tags': [],
                'target': [],
                'text': annotation['body'][0]['value'],
                'uri': annotation['target'],
        }

    for annotation in top_level:
        err_echo(json.dumps(top_level_payload(annotation), indent=2))
