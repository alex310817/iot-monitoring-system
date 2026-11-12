import styles from "../styles/components/button.module.scss";

interface CustomButtonProps {
  text: string;
  onClick?: () => void;
}

export default function CustomButton({ text, onClick }: CustomButtonProps) {
  return (
    <button className={styles.button} onClick={onClick}>
      {text}
    </button>
  );
}
