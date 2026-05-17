const useRazorpay = () => {
  const openPayment = ({ amount, name, description, onSuccess }) => {
    const options = {
      key: "rzp_test_YOUR_KEY_HERE",
      amount: amount * 100,        // convert ₹ to paise
      currency: "INR",
      name: name || "My App",
      description: description || "Payment",
      handler: function (response) {
        console.log("Payment ID:", response.razorpay_payment_id);
        onSuccess?.(response);
      },
      prefill: {
        name: "Test User",
        email: "test@example.com",
        contact: "9999999999",
      },
      theme: { color: "#00e054" },  // Letterboxd green :)
    };

    const rzp = new window.Razorpay(options);
    rzp.open();
  };

  return { openPayment };
};

export default useRazorpay;
