import Modal from './Modal';
import Button from './Button';

export default function ConfirmModal({ isOpen, onClose, onConfirm, title, message }) {
  const handleConfirm = () => {
    onConfirm();
    onClose();
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title || 'Confirm Action'}>
      <div className="space-y-4">
        <p className="text-[#E0E0E0]">{message}</p>
        <div className="flex gap-3 justify-end">
          <Button
            variant="secondary"
            onClick={onClose}
            data-testid="button-cancel-modal"
          >
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleConfirm}
            data-testid="button-confirm-modal"
          >
            Confirm
          </Button>
        </div>
      </div>
    </Modal>
  );
}

