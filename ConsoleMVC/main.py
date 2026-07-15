from ConsoleMVC.controllers.monitoring_controller import MonitoringController
from ConsoleMVC.controllers.order_controller import OrderController
from ConsoleMVC.controllers.production_controller import ProductionController
from ConsoleMVC.controllers.sample_controller import SampleController
from ConsoleMVC.controllers.shipment_controller import ShipmentController
from ConsoleMVC.models.order_repository import OrderRepository
from ConsoleMVC.models.production_line import ProductionLine
from ConsoleMVC.models.sample_repository import SampleRepository
from ConsoleMVC.views.main_view import MainView
from ConsoleMVC.views.monitoring_view import MonitoringView
from ConsoleMVC.views.order_view import OrderView
from ConsoleMVC.views.production_view import ProductionView
from ConsoleMVC.views.sample_view import SampleView
from ConsoleMVC.views.shipment_view import ShipmentView


def main() -> None:
    # 공유 저장소 (메모리 기반)
    sample_repo = SampleRepository()
    order_repo = OrderRepository()
    production_line = ProductionLine()

    main_view = MainView()

    sample_controller = SampleController(sample_repo, SampleView())
    order_controller = OrderController(order_repo, sample_repo, production_line, OrderView())
    monitoring_controller = MonitoringController(order_repo, sample_repo, MonitoringView())
    shipment_controller = ShipmentController(order_repo, sample_repo, ShipmentView())
    production_controller = ProductionController(production_line, order_repo, sample_repo, ProductionView())

    menu_actions = {
        "1": sample_controller.run,
        "2": order_controller.run,
        "3": monitoring_controller.run,
        "4": production_controller.run,
        "5": shipment_controller.run,
    }

    while True:
        choice = main_view.show_menu()
        if choice == "0":
            print("프로그램을 종료합니다.")
            break
        action = menu_actions.get(choice)
        if action:
            action()
        else:
            main_view.show_message("잘못된 입력입니다.")


if __name__ == "__main__":
    main()
