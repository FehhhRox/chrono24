"""
Chrono24 Data Analysis Module

This module provides functionality to analyze Chrono24 watch listings data,
including various aggregation functions for prices, shipping costs, and other metrics.
"""

import json
import statistics
from pathlib import Path
from typing import List, Dict, Optional, Union, Any


class Chrono24Analyzer:
    """Analyzer class for Chrono24 watch listings data."""

    def __init__(self, json_file_path: Union[str, Path]):
        """
        Initialize the analyzer with data from a JSON file.

        Args:
            json_file_path: Path to the JSON file containing listings data
        """
        self.json_file_path = Path(json_file_path)
        self.listings = []
        self._load_data()

    def _load_data(self):
        """Load data from the JSON file."""
        try:
            with open(self.json_file_path, "r", encoding="utf-8") as f:
                self.listings = json.load(f)
            print(f"Loaded {len(self.listings)} listings from {self.json_file_path}")
        except FileNotFoundError:
            raise FileNotFoundError(f"JSON file not found: {self.json_file_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON format in file: {self.json_file_path}")

    def _extract_price(self, price_str: str) -> Optional[float]:
        """
        Extract numeric price from price string (e.g., '$10,023' -> 10023.0).

        Args:
            price_str: Price string from the listing

        Returns:
            Numeric price value or None if parsing fails
        """
        if not price_str or price_str == "null":
            return None

        try:
            # Remove currency symbols and commas
            cleaned = (
                price_str.replace("$", "")
                .replace(",", "")
                .replace("€", "")
                .replace("£", "")
            )
            return float(cleaned)
        except (ValueError, AttributeError):
            return None

    def _get_valid_prices(self, price_type: str = "price") -> List[float]:
        """
        Get list of valid numeric prices from listings.

        Args:
            price_type: Type of price to extract ('price' or 'shipping_price')

        Returns:
            List of valid numeric prices
        """
        prices = []
        for listing in self.listings:
            price_value = self._extract_price(listing.get(price_type, ""))
            if price_value is not None:
                prices.append(price_value)
        return prices

    def _get_total_prices(self) -> List[float]:
        """Get list of total prices (price + shipping) for listings where both are available."""
        total_prices = []
        for listing in self.listings:
            price = self._extract_price(listing.get("price", ""))
            shipping = self._extract_price(listing.get("shipping_price", ""))

            if price is not None and shipping is not None:
                total_prices.append(price + shipping)
            elif price is not None and shipping is None:
                # If shipping is 0 or null, treat as 0
                total_prices.append(price)

        return total_prices

    def get_price_statistics(self) -> Dict[str, Union[float, int, str]]:
        """
        Get comprehensive price statistics.

        Returns:
            Dictionary containing price statistics
        """
        prices = self._get_valid_prices("price")

        if not prices:
            return {"error": "No valid prices found"}

        return {
            "count": len(prices),
            "average": statistics.mean(prices),
            "median": statistics.median(prices),
            "std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
            "min": min(prices),
            "max": max(prices),
            "variance": statistics.variance(prices) if len(prices) > 1 else 0,
        }

    def get_shipping_statistics(self) -> Dict[str, Union[float, int, str]]:
        """
        Get comprehensive shipping price statistics.

        Returns:
            Dictionary containing shipping price statistics
        """
        shipping_prices = self._get_valid_prices("shipping_price")

        if not shipping_prices:
            return {"error": "No valid shipping prices found"}

        return {
            "count": len(shipping_prices),
            "average": statistics.mean(shipping_prices),
            "median": statistics.median(shipping_prices),
            "std_dev": (
                statistics.stdev(shipping_prices) if len(shipping_prices) > 1 else 0
            ),
            "min": min(shipping_prices),
            "max": max(shipping_prices),
            "variance": (
                statistics.variance(shipping_prices) if len(shipping_prices) > 1 else 0
            ),
        }

    def get_total_price_statistics(self) -> Dict[str, Union[float, int, str]]:
        """
        Get comprehensive total price (price + shipping) statistics.

        Returns:
            Dictionary containing total price statistics
        """
        total_prices = self._get_total_prices()

        if not total_prices:
            return {"error": "No valid total prices found"}

        return {
            "count": len(total_prices),
            "average": statistics.mean(total_prices),
            "median": statistics.median(total_prices),
            "std_dev": statistics.stdev(total_prices) if len(total_prices) > 1 else 0,
            "min": min(total_prices),
            "max": max(total_prices),
            "variance": (
                statistics.variance(total_prices) if len(total_prices) > 1 else 0
            ),
        }

    def get_location_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics grouped by location.

        Returns:
            Dictionary with location-based statistics
        """
        location_data = {}

        for listing in self.listings:
            location = listing.get("location", "Unknown")
            price = self._extract_price(listing.get("price", ""))
            shipping = self._extract_price(listing.get("shipping_price", ""))

            if location not in location_data:
                location_data[location] = {"prices": [], "shipping": []}

            if price is not None:
                location_data[location]["prices"].append(price)
            if shipping is not None:
                location_data[location]["shipping"].append(shipping)

        # Calculate statistics for each location
        location_stats = {}
        for location, data in location_data.items():
            prices = data["prices"]
            shipping = data["shipping"]

            location_stats[location] = {
                "count": len(prices),
                "avg_price": statistics.mean(prices) if prices else 0,
                "avg_shipping": statistics.mean(shipping) if shipping else 0,
                "price_std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                "shipping_std_dev": (
                    statistics.stdev(shipping) if len(shipping) > 1 else 0
                ),
            }

        return location_stats

    def get_merchant_statistics(self) -> Dict[str, Dict]:
        """
        Get statistics grouped by merchant type.

        Returns:
            Dictionary with merchant-based statistics
        """
        merchant_data = {}

        for listing in self.listings:
            merchant = listing.get("merchant_name", "Unknown")
            price = self._extract_price(listing.get("price", ""))
            shipping = self._extract_price(listing.get("shipping_price", ""))

            if merchant not in merchant_data:
                merchant_data[merchant] = {"prices": [], "shipping": []}

            if price is not None:
                merchant_data[merchant]["prices"].append(price)
            if shipping is not None:
                merchant_data[merchant]["shipping"].append(shipping)

        # Calculate statistics for each merchant type
        merchant_stats = {}
        for merchant, data in merchant_data.items():
            prices = data["prices"]
            shipping = data["shipping"]

            merchant_stats[merchant] = {
                "count": len(prices),
                "avg_price": statistics.mean(prices) if prices else 0,
                "avg_shipping": statistics.mean(shipping) if shipping else 0,
                "price_std_dev": statistics.stdev(prices) if len(prices) > 1 else 0,
                "shipping_std_dev": (
                    statistics.stdev(shipping) if len(shipping) > 1 else 0
                ),
            }

        return merchant_stats

    def get_summary_report(self) -> Dict[str, Any]:
        """
        Get a comprehensive summary report of all statistics.

        Returns:
            Dictionary containing complete analysis summary
        """
        return {
            "dataset_info": {
                "total_listings": len(self.listings),
                "file_path": str(self.json_file_path),
            },
            "price_statistics": self.get_price_statistics(),
            "shipping_statistics": self.get_shipping_statistics(),
            "total_price_statistics": self.get_total_price_statistics(),
            "location_breakdown": self.get_location_statistics(),
            "merchant_breakdown": self.get_merchant_statistics(),
        }


# Convenience functions for quick analysis
def analyze_chrono24_data(json_file_path: Union[str, Path]) -> Chrono24Analyzer:
    """
    Create and return a Chrono24Analyzer instance.

    Args:
        json_file_path: Path to the JSON file containing listings data

    Returns:
        Chrono24Analyzer instance
    """
    return Chrono24Analyzer(json_file_path)


def get_price_summary(
    json_file_path: Union[str, Path],
) -> Dict[str, Union[float, int, str]]:
    """
    Quick function to get price statistics summary.

    Args:
        json_file_path: Path to the JSON file containing listings data

    Returns:
        Dictionary containing price statistics
    """
    analyzer = Chrono24Analyzer(json_file_path)
    return analyzer.get_price_statistics()


def get_shipping_summary(
    json_file_path: Union[str, Path],
) -> Dict[str, Union[float, int, str]]:
    """
    Quick function to get shipping price statistics summary.

    Args:
        json_file_path: Path to the JSON file containing listings data

    Returns:
        Dictionary containing shipping price statistics
    """
    analyzer = Chrono24Analyzer(json_file_path)
    return analyzer.get_shipping_statistics()


def get_total_price_summary(
    json_file_path: Union[str, Path],
) -> Dict[str, Union[float, int, str]]:
    """
    Quick function to get total price statistics summary.

    Args:
        json_file_path: Path to the JSON file containing listings data

    Returns:
        Dictionary containing total price statistics
    """
    analyzer = Chrono24Analyzer(json_file_path)
    return analyzer.get_total_price_statistics()


if __name__ == "__main__":
    # Example usage
    try:
        # Initialize analyzer with the JSON file
        json_path = "json_results/all_listings.json"
        analyzer = analyze_chrono24_data(json_path)

        # Print summary statistics
        print("=== CHRONO24 DATA ANALYSIS ===")
        print(f"Total listings: {len(analyzer.listings)}")
        print()

        # Price statistics
        price_stats = analyzer.get_price_statistics()
        print("PRICE STATISTICS:")
        for key, value in price_stats.items():
            if isinstance(value, float):
                print(f"  {key}: ${value:,.2f}")
            else:
                print(f"  {key}: {value}")
        print()

        # Shipping statistics
        shipping_stats = analyzer.get_shipping_statistics()
        print("SHIPPING STATISTICS:")
        for key, value in shipping_stats.items():
            if isinstance(value, float):
                print(f"  {key}: ${value:,.2f}")
            else:
                print(f"  {key}: {value}")
        print()

        # Total price statistics
        total_stats = analyzer.get_total_price_statistics()
        print("TOTAL PRICE STATISTICS (Price + Shipping):")
        for key, value in total_stats.items():
            if isinstance(value, float):
                print(f"  {key}: ${value:,.2f}")
            else:
                print(f"  {key}: {value}")

    except Exception as e:
        print(f"Error: {e}")
