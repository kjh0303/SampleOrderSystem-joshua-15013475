from ConsoleMVC.controllers.sample_controller import SampleController
from ConsoleMVC.models.sample_repository import SampleRepository


class FakeSampleView:
    def __init__(self, new_sample_input=None, search_keyword=""):
        self._new_sample_input = new_sample_input
        self._search_keyword = search_keyword
        self.messages = []
        self.shown_samples = None

    def input_new_sample(self):
        return self._new_sample_input

    def input_search_keyword(self):
        return self._search_keyword

    def show_samples(self, samples):
        self.shown_samples = samples

    def show_message(self, message):
        self.messages.append(message)


def test_register_sample_adds_to_repository_and_shows_success_message(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    view = FakeSampleView(new_sample_input=(1, "WaferA", 2.0, 0.9))
    controller = SampleController(repo, view)

    controller.register_sample()

    saved = repo.find_by_id(1)
    assert saved is not None
    assert saved.name == "WaferA"
    assert view.messages == ["[등록 완료] #1 WaferA"]


def test_register_sample_shows_cancel_message_when_input_is_none(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    view = FakeSampleView(new_sample_input=None)
    controller = SampleController(repo, view)

    controller.register_sample()

    assert repo.all() == []
    assert view.messages == ["등록이 취소되었습니다."]


def test_register_sample_shows_error_message_on_duplicate_id(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    repo.add(1, "WaferA", 2.0, 0.9)
    view = FakeSampleView(new_sample_input=(1, "WaferB", 3.0, 0.8))
    controller = SampleController(repo, view)

    controller.register_sample()

    assert len(repo.all()) == 1
    assert view.messages == ["이미 존재하는 시료 ID입니다. (ID: 1)"]


def test_list_samples_shows_all_samples_from_repository(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    repo.add(1, "WaferA", 2.0, 0.9)
    repo.add(2, "WaferB", 3.0, 0.8)
    view = FakeSampleView()
    controller = SampleController(repo, view)

    controller.list_samples()

    assert {s.sample_id for s in view.shown_samples} == {1, 2}


def test_search_samples_shows_only_matching_samples(tmp_path):
    repo = SampleRepository(tmp_path / "samples.json")
    repo.add(1, "8inch Wafer", 2.0, 0.9)
    repo.add(2, "SiC Sample", 2.0, 0.9)
    view = FakeSampleView(search_keyword="wafer")
    controller = SampleController(repo, view)

    controller.search_samples()

    assert [s.sample_id for s in view.shown_samples] == [1]
