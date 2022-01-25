import uuid
import datetime

from skyportal.tests import api


def test_add_and_retrieve_comment_group_id(
    comment_token, upload_data_token, public_source, public_group, lris
):
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': public_source.id,
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'text': 'Comment text',
            'group_ids': [public_group.id],
        },
        token=comment_token,
    )
    assert status == 200
    comment_id = data['data']['comment_id']

    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )

    assert status == 200
    assert data['data']['text'] == 'Comment text'


def test_add_and_retrieve_comment_group_access(
    comment_token_two_groups,
    upload_data_token_two_groups,
    public_source_two_groups,
    public_group2,
    public_group,
    comment_token,
    lris,
):
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source_two_groups.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': [public_group2.id],
        },
        token=upload_data_token_two_groups,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'text': 'Comment text',
            'group_ids': [public_group2.id],
        },
        token=comment_token_two_groups,
    )
    assert status == 200
    comment_id = data['data']['comment_id']

    # This token belongs to public_group2
    status, data = api(
        'GET',
        f'spectra/{spectrum_id}/comments/{comment_id}',
        token=comment_token_two_groups,
    )
    assert status == 200
    assert data['data']['text'] == 'Comment text'

    # This token does not belong to public_group2
    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 403

    # Both tokens should be able to view this comment, but not the underlying spectrum
    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'text': 'Comment text',
            'group_ids': [public_group.id, public_group2.id],
        },
        token=comment_token_two_groups,
    )
    assert status == 200
    comment_id = data['data']['comment_id']

    status, data = api(
        'GET',
        f'spectra/{spectrum_id}/comments/{comment_id}',
        token=comment_token_two_groups,
    )
    assert status == 200
    assert data['data']['text'] == 'Comment text'

    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 403  # the underlying spectrum is not accessible to group1

    # post a new spectrum with a comment, open to both groups
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source_two_groups.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': [public_group.id, public_group2.id],
        },
        token=upload_data_token_two_groups,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'text': 'New comment text',
            'group_ids': [public_group2.id],
        },
        token=comment_token_two_groups,
    )
    assert status == 200
    comment_id = data['data']['comment_id']

    # token for group1 can view the spectrum but cannot see comment
    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 403

    # Both tokens should be able to view comment after updating group list
    status, data = api(
        'PUT',
        f'spectra/{spectrum_id}/comments/{comment_id}',
        data={
            'text': 'New comment text',
            'group_ids': [public_group.id, public_group2.id],
        },
        token=comment_token_two_groups,
    )
    assert status == 200

    # the new comment on the new spectrum should now accessible
    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 200
    assert data['data']['text'] == 'New comment text'


def test_cannot_add_comment_without_permission(
    view_only_token, upload_data_token, public_source, lris
):
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': "all",
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'spectrum_id': spectrum_id,
            'text': 'Comment text',
        },
        token=view_only_token,
    )
    assert status == 401
    assert data['status'] == 'error'


def test_delete_comment(comment_token, upload_data_token, public_source, lris):
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': "all",
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'spectrum_id': spectrum_id,
            'text': 'Comment text',
        },
        token=comment_token,
    )
    assert status == 200
    comment_id = data['data']['comment_id']

    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 200
    assert data['data']['text'] == 'Comment text'

    # try to delete using the wrong spectrum ID
    status, data = api(
        'DELETE', f'spectra/{spectrum_id+1}/comments/{comment_id}', token=comment_token
    )
    assert status == 400
    assert (
        "Comment resource ID does not match resource ID given in path"
        in data["message"]
    )

    status, data = api(
        'DELETE', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 200

    status, data = api(
        'GET', f'spectra/{spectrum_id}/comments/{comment_id}', token=comment_token
    )
    assert status == 403


def test_post_comment_attachment(super_admin_token, public_source, lris, public_group):

    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': "all",
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    payload = {
        "body": "eyJ0aW1lc3RhbXAiOiAiMjAyMC0xMS0wNFQxMjowMDowMyIsICJydW4iOiAxODM5LCAiZHVyYXRpb24iOiAwLjE0NiwgInJlc3VsdCI6IHsibW9kZWwiOiAic2FsdDIiLCAiZml0X2xjX3BhcmFtZXRlcnMiOiB7ImJvdW5kcyI6IHsiYyI6IFstMiwgNV0sICJ4MSI6IFstNSwgNV0sICJ6IjogWzAsIDAuMl19fSwgImZpdF9hY2NlcHRhYmxlIjogZmFsc2UsICJwbG90X2luZm8iOiAic2FsdDIgY2hpc3EgMjAuMjkgbmRvZiAxIG9rIGZpdCBGYWxzZSIsICJtb2RlbF9hbmFseXNpcyI6IHsiaGFzX3ByZW1heF9kYXRhIjogdHJ1ZSwgImhhc19wb3N0bWF4X2RhdGEiOiBmYWxzZSwgIngxX2luX3JhbmdlIjogdHJ1ZSwgIl94MV9yYW5nZSI6IFstNCwgNF0sICJjX29rIjogdHJ1ZSwgIl9jX3JhbmdlIjogWy0xLCAyXX0sICJmaXRfcmVzdWx0cyI6IHsieiI6IDAuMTE3NDM5NTYwNTE3MDEwNjUsICJ0MCI6IDI0NTkxNTguODE5NzYyNTE2MywgIngwIjogMC4wMDA2MDg1NTg3NzI2MjI5NDY3LCAieDEiOiAtMC44NzM1ODM5NTY4MTk5NjczLCAiYyI6IC0wLjA1OTg1NTgxMTY2MDA2MzE1LCAibXdlYnYiOiAwLjA5OTU2MTk1NjAzOTAzMTEyLCAibXdyX3YiOiAzLjEsICJ6LmVyciI6IDAuMDIxNTUyNTQwMzEyMzk1NDI0LCAidDAuZXJyIjogMC45NTczNDkzNTY0OTY3MDY2LCAieDAuZXJyIjogNi43NDYwMTY5NDY3ODk5NDllLTA1LCAieDEuZXJyIjogMC42NDc4NTA5NzU5ODY5OTY2LCAiYy5lcnIiOiAwLjEzNDQxMzAzNjM5NjQxMzU1fSwgInNuY29zbW9faW5mbyI6IHsic3VjY2VzcyI6IHRydWUsICJjaGlzcSI6IDIwLjI5NDAxNzkxMDExMjMxMywgIm5kb2YiOiAxLCAiY2hpc3Fkb2YiOiAyMC4yOTQwMTc5MTAxMTIzMTN9LCAiZmx1eF9kaWN0IjogeyJ6dGZnIjogWzAuMCwgLTAuMDQyNjA1ODU1NzUwNDczMzYsIC0wLjE1OTc2MzYxMjQ2NDMxOTQyLCAtMC41MDU5ODM5ODUzNTUyNDg1LCAtMC4xMDU5NzkwNDU0NzgyOTA4MywgMy44MjIzMDg5NDc0ODQ1NzEsIDEyLjE5Njc1NDg2NzEwMDE0NywgMjMuODgzNTQ0OTEzNTM0MTUsIDM4LjIyMzIzMjgyMDM3NzUyLCA1NS4wMTU0NjcyNzgyNzMwOCwgNzQuMzQyNTQxNDE2MzQ5MjIsIDk2LjMyNzQ1MzkzMzE2MDA5LCAxMjEuMjMwODU1MjE3MTg2ODMsIDE0OS42NzE5NzMzNDU4Mzg4NiwgMTc4LjU4NzEzMzY3MjU1MDI3LCAyMDUuMDcyMDU1NjU4Nzg4NDYsIDIyOC4wNTUzMTYwNjg0MjQsIDI0Ny4zNTIzMjM5ODA4Nzg1NywgMjYyLjYwOTI1MTk2MzQ1NzMsIDI3My45NjAxOTExOTE4NTEsIDI4Mi4wMTYzOTE3NTE3NzMsIDI4Ni4zNzI2Mjg3NjU4NjE2MywgMjg2LjY4ODcwMTAxODEzNDQ1LCAyODMuNTU0NTY3MTE3MzQ4MSwgMjc3LjY5MjY0NTUyNDYwODgsIDI2OS40ODM1NDU5ODQ2MTMzLCAyNTkuMTAxNDEyMTkxMjIwOCwgMjQ2Ljk2OTEyOTQ0OTc2NTE1LCAyMzMuODk5MTY4NzM2OTE5MjgsIDIyMC4xMzIyNzI0NjI2MDgzNCwgMjA1LjcxNjY4NzM5MzQxMzE0LCAxOTAuNTk3MTUyMDAzOTQzODUsIDE3NS41NTM4NDE0NDAyMjYyMiwgMTYxLjE2NTk5Mzk2NDQ1NDMyLCAxNDcuNTEwNTE3ODIyNjI0MTcsIDEzNC40NDYyMjA0NjIxODY5NCwgMTIxLjg5NDI1MDE3MDAxNDM5LCAxMDkuOTA0OTI2NzQzMDg2NzIsIDk4Ljg1ODU4MjA1NTk5MDE0LCA4OC44MjIyNDkyNDQ5ODgwNiwgNzkuODU1NDY1Nzk5NzkzOTMsIDcyLjA5NTcyMzMzMTQ2NzIsIDY1LjMwMjgyMzM5NDQzNzU3LCA1OS4yNTMxMjgyMDM2MzYzNDQsIDUzLjkyNjI2NjAzMjI5NDUyLCA0OS40MTk3OTAzMTc3NTMyOCwgNDUuNjc4NTQ4MjU5MDMwNjQsIDQyLjMxMjkyMDczNTM0MDk3LCAzOS4xMzUwNDI0OTI2NjEzMSwgMzYuMTc1NTQ2NTcyMTI5NywgMzMuNDI4OTg3OTU4MTgzNDUsIDMwLjkyODcxOTcyNjIzMzE4NywgMjguNzUyMjgxODYxNTg1NjQsIDI2LjkwMjQ3ODU5MDAzMDA5NiwgMjUuMzMzOTc4MzQ4MzEyMzYsIDI0LjAxMTA1NjIzOTM4MjkzNSwgMjIuOTAzODgyMjIyNjQwNTU0LCAyMS45ODU1MjExMDM5NjA1NTgsIDIxLjE4MzYxNTc5ODI1OTE3MiwgMjAuNDUyMjYzMDY5MTMwNDY3LCAxOS43ODQ2NDgxNDA4MjM3NTUsIDE5LjE3NTU1OTc1NTQwMzQyNywgMTguNjIwMzc0ODc2NTc1MjksIDE4LjExNTA4NTAxNDE3MjMxNSwgMTcuNjU2MjcwMzk5NzY4MzIsIDE3LjI0MDMyMDg1NjEyNTk5LCAxNi44NTkxMTMwMzUwMTQ1NzcsIDE2LjQ4NjE4ODc2Njc0MTY5OCwgMTYuMTE4OTQwODAyOTc3MDQ3LCAxNS43NTg0NzM3NDM2NDc4NjIsIDE1LjQwNTc0NTcwNDAwMTI0NiwgMTUuMDYxNzIzMzM0MjQ2MDQzLCAxNC43MjczODEwMjI5Nzk4MDQsIDE0LjQwMzY5NTMxNTY1OTUzLCAxNC4wOTE2Mzk5MTExNzczNTMsIDEzLjc5MjE4MTE0NDkwNTA1OCwgMTMuNTA2MjczODY5OTM1ODA3LCAxMy4yMzQ4Njg0ODM3Njc1MzksIDEyLjk4MTU3MzMxODc4OTYyN10sICJ6dGZyIjogWzAuMCwgMC4yMDkwMjkyNzU5Mzc3MzQ5LCAwLjc4ODc0NjQ5ODgxMDcwMzksIDEuNzIyNTcyMDQ5MDAyNDYxNCwgMy42OTI5MjkzMjcwMDQxNDMyLCA4Ljc5MDcxNTY1MDg1NDgwNSwgMTcuNjMyNDU0MDIxMTYyMzM1LCAyOS4yNTAwMTgzNTEwOTI2MTcsIDQzLjA2OTYyOTQwMjAzMDcxLCA1OC44MjcyMTA3OTA5ODU1NywgNzYuNDg2NjMwNDI0MzgxMzksIDk2LjE5OTQ4Mzk4ODEwOTcyLCAxMTguMjA0MzUzMTc5NjA4NSwgMTQzLjAwNzYzODUwNjUxMDY2LCAxNjguMzEyOTYwNzk1NjcyMDQsIDE5MS45NDMxNTA1MTU0NTUwNywgMjEzLjExMjQ5MjAxODQ1MDMsIDIzMS43MDU4NjcwOTQ1MjU0MiwgMjQ3LjQ3Nzg0MDIwMzIxNTYsIDI2MC41NjYzOTUwNzY4NzIzNywgMjcxLjQ3ODE4NDY2MTkwMjcsIDI3OS44ODk5NTU4MjU4NTQ1NCwgMjg1LjUzNjM3MjA2NjA5NTA1LCAyODguNTYwNDMyMzQ4MTA3ODQsIDI4OS4yMDkxODAzODM0NjU1LCAyODcuNjUwMjExNzU1NDQxNywgMjg0LjAxMjM5MTM1MDM1NTcsIDI3OC40MDEyNzQyOTkwNjQ1LCAyNzAuNzQ3ODQ1MjM1ODM2MTcsIDI2MS4yMDkzMzY3NjQxOTcyLCAyNDkuOTY1NDI1MjA5MDkzNjQsIDIzNi45OTYwODA4NDE3NDY1NiwgMjIzLjgyMjE4ODMwMjU3MjMsIDIxMS42MDIyMzAxOTM5NTMzMiwgMjAwLjU3Njg4NDg1MTY3NjUsIDE5MC41OTQ5NzcwNDMxMDUzMywgMTgxLjU4NjIyMjIwNDI1NTUzLCAxNzMuNDE4MDQxNzE4Nzc0NzMsIDE2NS43MzA3MDQ1NzY4OTE4NCwgMTU4LjQ4MjI5NTMyNDg2NTAyLCAxNTEuNjk5NTg5MDg1MzM3ODYsIDE0NS40NTE4MTQ5NDI5MDg2NywgMTM5LjU4NDA3NTMzMzM1MzIsIDEzMy45NTkxODY4MzI4Njg3NywgMTI4LjU3MzUxMzA2ODM0MDUsIDEyMy41MTE2ODQ3MzA1NTI0LCAxMTguNzIxNzkwNTIxMTI0MTMsIDExMy44MDQ0MDc3MTY2NDgyOSwgMTA4LjYwODM1NTg2NDcxNzEzLCAxMDMuMjQxMzg2NjgzMDIxNDUsIDk3Ljc2NTI0NjgyMjU0MDA4LCA5Mi4zMzM3MTQxNjc3MjA4MSwgODcuMTk3NDkyMjAyMTk5MDQsIDgyLjQyODMxMDQ2NDc4ODMyLCA3Ny45Nzc5MjUyNzYzNzA4OCwgNzMuODEwMDcxNTY1NjgzNjMsIDY5Ljg5MTk0NDMyNjg0OSwgNjYuMTk5MzM4MTkxNjMwNCwgNjIuODE0MDY4Mjk4NzQ1Njk2LCA1OS43NzUwOTExMzk3MjA2MywgNTcuMDUxMDcyNjc2ODk3MTUsIDU0LjYxNDMxOTc2NDU2NTM0NCwgNTIuNDQxMzM3NjgzNjU1NjYsIDUwLjUxMTUyNzYyMjUyMDkyLCA0OC44MDY4ODUwNDEwMjEyMiwgNDcuMzA5MjE5ODg4NjkxNjE1LCA0NS45ODU1MTU2NDIxNDYxNywgNDQuNzQxNDAwNjkzNDQ3MDQsIDQzLjU2MjcwOTkyODYwOTE2NiwgNDIuNDQ3OTkwOTkzNDI2OTksIDQxLjM5NTQ1MDExNjg4MzUsIDQwLjQwMzQzMDc2MDk2MTY4LCAzOS40NzA0MDYxMjgyMjcyNCwgMzguNTk0OTYwNzIwNjY3NCwgMzcuNzc1Nzc3NzI1ODY5OTQsIDM3LjAxMTYzMDk2NDg1NDUyNSwgMzYuMzAxMzgwMzgzNDY1NjU2LCAzNS42NDM5NTk0MzY0NjcxNSwgMzUuMDQzODYwODA3MzQ5ODk0XSwgIm9ic2pkIjogWzI0NTkxMzYuNDcwOTcxMzA2LCAyNDU5MTM3LjQ3MDk3MTMwNiwgMjQ1OTEzOC40NzA5NzEzMDYsIDI0NTkxMzkuNDcwOTcxMzA2LCAyNDU5MTQwLjQ3MDk3MTMwNiwgMjQ1OTE0MS40NzA5NzEzMDYsIDI0NTkxNDIuNDcwOTcxMzA2LCAyNDU5MTQzLjQ3MDk3MTMwNiwgMjQ1OTE0NC40NzA5NzEzMDYsIDI0NTkxNDUuNDcwOTcxMzA2LCAyNDU5MTQ2LjQ3MDk3MTMwNiwgMjQ1OTE0Ny40NzA5NzEzMDYsIDI0NTkxNDguNDcwOTcxMzA2LCAyNDU5MTQ5LjQ3MDk3MTMwNiwgMjQ1OTE1MC40NzA5NzEzMDYsIDI0NTkxNTEuNDcwOTcxMzA2LCAyNDU5MTUyLjQ3MDk3MTMwNiwgMjQ1OTE1My40NzA5NzEzMDYsIDI0NTkxNTQuNDcwOTcxMzA2LCAyNDU5MTU1LjQ3MDk3MTMwNiwgMjQ1OTE1Ni40NzA5NzEzMDYsIDI0NTkxNTcuNDcwOTcxMzA2LCAyNDU5MTU4LjQ3MDk3MTMwNiwgMjQ1OTE1OS40NzA5NzEzMDYsIDI0NTkxNjAuNDcwOTcxMzA2LCAyNDU5MTYxLjQ3MDk3MTMwNiwgMjQ1OTE2Mi40NzA5NzEzMDYsIDI0NTkxNjMuNDcwOTcxMzA2LCAyNDU5MTY0LjQ3MDk3MTMwNiwgMjQ1OTE2NS40NzA5NzEzMDYsIDI0NTkxNjYuNDcwOTcxMzA2LCAyNDU5MTY3LjQ3MDk3MTMwNiwgMjQ1OTE2OC40NzA5NzEzMDYsIDI0NTkxNjkuNDcwOTcxMzA2LCAyNDU5MTcwLjQ3MDk3MTMwNiwgMjQ1OTE3MS40NzA5NzEzMDYsIDI0NTkxNzIuNDcwOTcxMzA2LCAyNDU5MTczLjQ3MDk3MTMwNiwgMjQ1OTE3NC40NzA5NzEzMDYsIDI0NTkxNzUuNDcwOTcxMzA2LCAyNDU5MTc2LjQ3MDk3MTMwNiwgMjQ1OTE3Ny40NzA5NzEzMDYsIDI0NTkxNzguNDcwOTcxMzA2LCAyNDU5MTc5LjQ3MDk3MTMwNiwgMjQ1OTE4MC40NzA5NzEzMDYsIDI0NTkxODEuNDcwOTcxMzA2LCAyNDU5MTgyLjQ3MDk3MTMwNiwgMjQ1OTE4My40NzA5NzEzMDYsIDI0NTkxODQuNDcwOTcxMzA2LCAyNDU5MTg1LjQ3MDk3MTMwNiwgMjQ1OTE4Ni40NzA5NzEzMDYsIDI0NTkxODcuNDcwOTcxMzA2LCAyNDU5MTg4LjQ3MDk3MTMwNiwgMjQ1OTE4OS40NzA5NzEzMDYsIDI0NTkxOTAuNDcwOTcxMzA2LCAyNDU5MTkxLjQ3MDk3MTMwNiwgMjQ1OTE5Mi40NzA5NzEzMDYsIDI0NTkxOTMuNDcwOTcxMzA2LCAyNDU5MTk0LjQ3MDk3MTMwNiwgMjQ1OTE5NS40NzA5NzEzMDYsIDI0NTkxOTYuNDcwOTcxMzA2LCAyNDU5MTk3LjQ3MDk3MTMwNiwgMjQ1OTE5OC40NzA5NzEzMDYsIDI0NTkxOTkuNDcwOTcxMzA2LCAyNDU5MjAwLjQ3MDk3MTMwNiwgMjQ1OTIwMS40NzA5NzEzMDYsIDI0NTkyMDIuNDcwOTcxMzA2LCAyNDU5MjAzLjQ3MDk3MTMwNiwgMjQ1OTIwNC40NzA5NzEzMDYsIDI0NTkyMDUuNDcwOTcxMzA2LCAyNDU5MjA2LjQ3MDk3MTMwNiwgMjQ1OTIwNy40NzA5NzEzMDYsIDI0NTkyMDguNDcwOTcxMzA2LCAyNDU5MjA5LjQ3MDk3MTMwNiwgMjQ1OTIxMC40NzA5NzEzMDYsIDI0NTkyMTEuNDcwOTcxMzA2LCAyNDU5MjEyLjQ3MDk3MTMwNiwgMjQ1OTIxMy40NzA5NzEzMDYsIDI0NTkyMTQuNDcwOTcxMzA2XX19fQ==",
        "name": "ampel_test.json",
    }
    # note: the attachment_bytes is base64 encoded. The values are a json with a fit to a lightcurve: {"timestamp": "2020-11-04T12:00:03", "run": 1839, "duration": 0.146, "result": {"model": "salt2", "fit_lc_parameters": {"bounds": {"c": [-2, 5], "x1": [-5, 5], "z": [0, 0.2]}}, "fit_acceptable": false, "plot_info": "salt2 chisq 20.29 ndof 1 ok fit False", "model_analysis": {"has_premax_data": true, "has_postmax_data": false, "x1_in_range": true, "_x1_range": [-4, 4], "c_ok": true, "_c_range": [-1, 2]}, "fit_results": {"z": 0.11743956051701065, "t0": 2459158.8197625163, "x0": 0.0006085587726229467, "x1": -0.8735839568199673, "c": -0.05985581166006315, "mwebv": 0.09956195603903112, "mwr_v": 3.1, "z.err": 0.021552540312395424, "t0.err": 0.9573493564967066, "x0.err": 6.746016946789949e-05, "x1.err": 0.6478509759869966, "c.err": 0.13441303639641355}, "sncosmo_info": {"success": true, "chisq": 20.294017910112313, "ndof": 1, "chisqdof": 20.294017910112313}, "flux_dict": {"ztfg": [0.0, -0.04260585575047336, -0.15976361246431942, -0.5059839853552485, -0.10597904547829083, 3.822308947484571, 12.196754867100147, 23.88354491353415, 38.22323282037752, 55.01546727827308, 74.34254141634922, 96.32745393316009, 121.23085521718683, 149.67197334583886, 178.58713367255027, 205.07205565878846, 228.055316068424, 247.35232398087857, 262.6092519634573, 273.960191191851, 282.016391751773, 286.37262876586163, 286.68870101813445, 283.5545671173481, 277.6926455246088, 269.4835459846133, 259.1014121912208, 246.96912944976515, 233.89916873691928, 220.13227246260834, 205.71668739341314, 190.59715200394385, 175.55384144022622, 161.16599396445432, 147.51051782262417, 134.44622046218694, 121.89425017001439, 109.90492674308672, 98.85858205599014, 88.82224924498806, 79.85546579979393, 72.0957233314672, 65.30282339443757, 59.253128203636344, 53.92626603229452, 49.41979031775328, 45.67854825903064, 42.31292073534097, 39.13504249266131, 36.1755465721297, 33.42898795818345, 30.928719726233187, 28.75228186158564, 26.902478590030096, 25.33397834831236, 24.011056239382935, 22.903882222640554, 21.985521103960558, 21.183615798259172, 20.452263069130467, 19.784648140823755, 19.175559755403427, 18.62037487657529, 18.115085014172315, 17.65627039976832, 17.24032085612599, 16.859113035014577, 16.486188766741698, 16.118940802977047, 15.758473743647862, 15.405745704001246, 15.061723334246043, 14.727381022979804, 14.40369531565953, 14.091639911177353, 13.792181144905058, 13.506273869935807, 13.234868483767539, 12.981573318789627], "ztfr": [0.0, 0.2090292759377349, 0.7887464988107039, 1.7225720490024614, 3.6929293270041432, 8.790715650854805, 17.632454021162335, 29.250018351092617, 43.06962940203071, 58.82721079098557, 76.48663042438139, 96.19948398810972, 118.2043531796085, 143.00763850651066, 168.31296079567204, 191.94315051545507, 213.1124920184503, 231.70586709452542, 247.4778402032156, 260.56639507687237, 271.4781846619027, 279.88995582585454, 285.53637206609505, 288.56043234810784, 289.2091803834655, 287.6502117554417, 284.0123913503557, 278.4012742990645, 270.74784523583617, 261.2093367641972, 249.96542520909364, 236.99608084174656, 223.8221883025723, 211.60223019395332, 200.5768848516765, 190.59497704310533, 181.58622220425553, 173.41804171877473, 165.73070457689184, 158.48229532486502, 151.69958908533786, 145.45181494290867, 139.5840753333532, 133.95918683286877, 128.5735130683405, 123.5116847305524, 118.72179052112413, 113.80440771664829, 108.60835586471713, 103.24138668302145, 97.76524682254008, 92.33371416772081, 87.19749220219904, 82.42831046478832, 77.97792527637088, 73.81007156568363, 69.891944326849, 66.1993381916304, 62.814068298745696, 59.77509113972063, 57.05107267689715, 54.614319764565344, 52.44133768365566, 50.51152762252092, 48.80688504102122, 47.309219888691615, 45.98551564214617, 44.74140069344704, 43.562709928609166, 42.44799099342699, 41.3954501168835, 40.40343076096168, 39.47040612822724, 38.5949607206674, 37.77577772586994, 37.011630964854525, 36.301380383465656, 35.64395943646715, 35.043860807349894], "obsjd": [2459136.470971306, 2459137.470971306, 2459138.470971306, 2459139.470971306, 2459140.470971306, 2459141.470971306, 2459142.470971306, 2459143.470971306, 2459144.470971306, 2459145.470971306, 2459146.470971306, 2459147.470971306, 2459148.470971306, 2459149.470971306, 2459150.470971306, 2459151.470971306, 2459152.470971306, 2459153.470971306, 2459154.470971306, 2459155.470971306, 2459156.470971306, 2459157.470971306, 2459158.470971306, 2459159.470971306, 2459160.470971306, 2459161.470971306, 2459162.470971306, 2459163.470971306, 2459164.470971306, 2459165.470971306, 2459166.470971306, 2459167.470971306, 2459168.470971306, 2459169.470971306, 2459170.470971306, 2459171.470971306, 2459172.470971306, 2459173.470971306, 2459174.470971306, 2459175.470971306, 2459176.470971306, 2459177.470971306, 2459178.470971306, 2459179.470971306, 2459180.470971306, 2459181.470971306, 2459182.470971306, 2459183.470971306, 2459184.470971306, 2459185.470971306, 2459186.470971306, 2459187.470971306, 2459188.470971306, 2459189.470971306, 2459190.470971306, 2459191.470971306, 2459192.470971306, 2459193.470971306, 2459194.470971306, 2459195.470971306, 2459196.470971306, 2459197.470971306, 2459198.470971306, 2459199.470971306, 2459200.470971306, 2459201.470971306, 2459202.470971306, 2459203.470971306, 2459204.470971306, 2459205.470971306, 2459206.470971306, 2459207.470971306, 2459208.470971306, 2459209.470971306, 2459210.470971306, 2459211.470971306, 2459212.470971306, 2459213.470971306, 2459214.470971306]}}}

    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={
            'text': 'Looks like Ia',
            'group_ids': [public_group.id],
            "attachment": payload,
        },
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'

    status, data = api(
        'GET',
        f'spectra/{spectrum_id}/comments/{data["data"]["comment_id"]}',
        token=super_admin_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    assert data['data']['text'] == 'Looks like Ia'
    assert data['data']['attachment_bytes'] == payload['body']
    assert data['data']['attachment_name'] == payload['name']


def test_fetch_all_comments_on_obj(
    upload_data_token, comment_token, public_source, lris
):
    status, data = api(
        'POST',
        'spectrum',
        data={
            'obj_id': str(public_source.id),
            'observed_at': str(datetime.datetime.now()),
            'instrument_id': lris.id,
            'wavelengths': [664, 665, 666],
            'fluxes': [234.2, 232.1, 235.3],
            'group_ids': "all",
        },
        token=upload_data_token,
    )
    assert status == 200
    assert data['status'] == 'success'
    spectrum_id = data["data"]["id"]

    comment_text = str(uuid.uuid4())
    status, data = api(
        'POST',
        f'spectra/{spectrum_id}/comments',
        data={'text': comment_text},
        token=comment_token,
    )
    assert status == 200

    status, data = api('GET', f'spectra/{spectrum_id}/comments', token=comment_token)

    assert status == 200
    assert any([comment['text'] == comment_text for comment in data['data']])
