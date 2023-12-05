kubectl --kubeconfig ./do/fbs-kubeconfig.yaml delete -f ./kubernetes/worker-controller.yaml
kubectl --kubeconfig ./do/fbs-kubeconfig.yaml create -f ./kubernetes/worker-controller.yaml
