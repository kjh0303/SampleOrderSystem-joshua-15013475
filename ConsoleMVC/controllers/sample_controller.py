from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.sample_view import SampleView


class SampleController:
    """시료 등록 / 목록 조회 / 이름 검색을 처리"""

    def __init__(self, sample_repo: SampleRepository, view: SampleView):
        self._repo = sample_repo
        self._view = view

    def register_sample(self) -> None:
        result = self._view.input_new_sample()
        if result is None:
            self._view.show_message("등록이 취소되었습니다.")
            return
        sample_id, name, avg_production_time, yield_rate = result
        try:
            sample = self._repo.add(sample_id, name, avg_production_time, yield_rate)
        except ValueError as e:
            self._view.show_message(str(e))
            return
        self._view.show_message(f"[등록 완료] #{sample.sample_id} {sample.name}")

    def list_samples(self) -> None:
        samples = self._repo.all()
        self._view.show_samples(samples)

    def search_samples(self) -> None:
        keyword = self._view.input_search_keyword()
        results = self._repo.find_by_name(keyword)
        self._view.show_samples(results)

    def run(self) -> None:
        while True:
            choice = self._view.show_menu()
            if choice == "1":
                self.register_sample()
            elif choice == "2":
                self.list_samples()
            elif choice == "3":
                self.search_samples()
            elif choice == "0":
                break
            else:
                self._view.show_message("잘못된 입력입니다.")
